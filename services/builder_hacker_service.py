import os
import logging
import tempfile
import subprocess
from typing import Optional, List

from agents.builder_agent import BuilderAgent
from agents.hacker_agent import HackerAgent


class BuilderHackerService:
    def __init__(
        self,
        project_root_path: str,
        olympix_path: str,
        builder_temp: int = 1,
        hacker_temp: int = 1,        
        test_skeleton_path: Optional[str] = None,
        exploit_skeleton_path: Optional[str] = None
    ):
        """
        Initialize the BuilderHackerService.

        :param project_root_path: Root path of the Forge project.
        :param olympix_path: Path to the olympix.exe tool.
        :param hacker_temp: Temperature parameter for the GPT model (creativity).
        :param test_skeleton: Optional base skeleton for test generation.
        """
        self.project_root_path = project_root_path
        self.olympix_path = olympix_path

        self.builder_agent = BuilderAgent(
            gpt_model='o1',
            forge_path=project_root_path,
            olympix_path=olympix_path,
            temp=builder_temp,
            test_skeleton_path=test_skeleton_path
        )

        self.hacker_agent = HackerAgent(
            gpt_model='o1',
            forge_path=project_root_path,
            temp=hacker_temp,
            exploit_skeleton_path=exploit_skeleton_path
        )

        self.src_path = os.path.join(self.project_root_path, "src")
        self.test_path = os.path.join(self.project_root_path, "test")
        self.exploit_path = os.path.join(self.project_root_path, "exploits")

        # Ensure that test directory exists
        os.makedirs(self.test_path, exist_ok=True)

        logging.info("BuilderHackerService initialized successfully.")


    def build(self, filename: str, attempts: int = 3) -> bool:
        """
        Creates test contract for the specified filename.
        Retries up to 'attempts' times for each file until a valid test contract is generated.

        :param filename: Name of the Solidity file to generate tests for. If None, all .sol files are processed.
        :param attempts: Number of attempts to generate a valid test contract per file.
        :return: Boolean indicating whether all test file generations were successful.
        :raises RuntimeError: If test file generation fails after the specified number of attempts.
        """
        logging.info(f"Starting test generation process...")
        success = False
        target_files: List[str] = []

        if filename:
            # Normalize filename
            if not filename.endswith(".sol"):
                filename += ".sol"
            target_files = [filename]
        else:
            # Process all .sol files in src/
            target_files = [f for f in os.listdir(self.src_path) if f.endswith(".sol")]

        for file in target_files:
            logging.info(f"Generating test for file: {file}")
            for attempt in range(1, attempts + 1):
                try:
                    generated_tests = self.tester_agent.generate_test(file)
                    test_filename, test_code = next(iter(generated_tests.items()))
                    logging.debug(f"Generated test code for {test_filename} on attempt {attempt}")

                    if self._is_test_code_valid(test_code):
                        logging.info(f"Valid test code generated for {test_filename} on attempt {attempt}")
                        success =  True
                        break  # Exit the retry loop for this file
                    else:
                        logging.warning(f"Invalid test code generated for {test_filename} on attempt {attempt}")
                        success = False
                except Exception as e:
                    logging.error(f"Error generating test for {file} on attempt {attempt}: {e}")

                if attempt == attempts:
                    error_msg = f"Failed to generate a valid test for '{file}' after {attempts} attempts."
                    logging.error(error_msg)
                    success = False
                    # raise RuntimeError(error_msg)

        logging.info("Test generation completed.")
        return success


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
