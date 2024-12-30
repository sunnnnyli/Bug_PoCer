import os
import logging
import tempfile
import subprocess
from typing import Optional, List

from agents.tester_agent import TesterAgent


class TesterService:
    def __init__(
        self,
        project_root_path: str,
        olympix_path: str,
        temp: int = 1,
    ):
        """
        Initialize the TesterService.

        :param project_root_path: Root path of the Forge project.
        :param olympix_path: Path to the olympix.exe tool.
        :param hacker_temp: Temperature parameter for the GPT model (creativity).
        :param test_skeleton: Optional base skeleton for test generation.
        """
        self.project_root_path = project_root_path
        self.olympix_path = olympix_path
        self.temp = temp

        self.tester_agent = TesterAgent(
            gpt_model='o1',
            forge_path=project_root_path,
            temp=temp,
        )

        self.src_path = os.path.join(self.project_root_path, "src")
        self.test_path = os.path.join(self.project_root_path, "test")

        # Ensure that test directory exists
        os.makedirs(self.test_path, exist_ok=True)

        logging.info("TesterService initialized successfully.")


    def execute(self, filename: Optional[str] = None) -> bool:
        """
        Executes the test file for the specified filename.

        :param filename: Name of the Solidity test file to execute. If None, all test files are executed.
        :return: Boolean indicating whether all tests passed successfully.
        """
        logging.info(f"Starting test execution process...")
        all_tests_passed = True
        target_tests: List[str] = []

        if filename:
            # Normalize test filename
            if not filename.endswith("Test.sol"):
                base_name = os.path.splitext(filename)[0]
                filename = f"{base_name}Test.sol"
            target_tests = [filename]
        else:
            # Execute all test files in test/
            target_tests = [f for f in os.listdir(self.test_path) if f.endswith("Test.sol")]

        for test_file in target_tests:
            try:
                logging.info(f"Running test: {test_file}")
                test_passed = self.tester_agent.run_test(test_file)
                if not test_passed:
                    all_tests_passed = False
            except Exception as e:
                logging.error(f"Error executing test '{test_file}': {e}")
                all_tests_passed = False

        if all_tests_passed:
            logging.info("All tests passed successfully.")
        else:
            logging.warning("Some tests failed. Check logs for details.")

        return all_tests_passed


    def _is_test_code_valid(self, test_code: str) -> bool:
        """
        Validates the generated test code by performing linting with Solhint and compiling with Forge.

        :param test_code: The Solidity test contract code to validate.
        :return: Boolean indicating whether the test code is valid.
        """
        logging.info("Validating test code...")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sol', delete=False) as temp_file:
            temp_filename = temp_file.name
            temp_file.write(test_code)
            logging.debug(f"Test code written to temporary file: {temp_filename}")

        try:
            # Compile the test contract using Forge
            forge_cmd = ["forge", "build", temp_filename]
            logging.info(f"Running Forge compile: {' '.join(forge_cmd)}")
            forge_result = subprocess.run(
                forge_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.project_root_path
            )

            if forge_result.returncode != 0:
                logging.warning(f"Forge compilation failed for {temp_filename}:\n{forge_result.stderr}")
                return False
            else:
                logging.info("Forge compilation succeeded.")

            return True

        except FileNotFoundError as e:
            logging.error(f"Required tool not found: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error during test code validation: {e}")
            return False
        finally:
            # Clean up the temporary file
            try:
                os.remove(temp_filename)
                logging.debug(f"Temporary file {temp_filename} removed.")
            except OSError as e:
                logging.warning(f"Could not remove temporary file {temp_filename}: {e}")
