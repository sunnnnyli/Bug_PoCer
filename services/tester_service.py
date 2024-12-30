import os
import logging

from agents.tester_agent import TesterAgent


class TesterService:
    def __init__(
        self,
        project_root_path: str,
        temp: int = 1,
    ):
        """
        Initialize the TesterService.

        :param project_root_path: Root path of the Forge project.
        :param hacker_temp: Temperature parameter for the GPT model (creativity).
        :param test_skeleton: Optional base skeleton for test generation.
        """
        self.project_root_path = project_root_path
        self.temp = temp

        self.tester_agent = TesterAgent(
            gpt_model='o1',
            forge_path=project_root_path,
            temp=temp,
        )

        self.test_path = os.path.join(self.project_root_path, "test")

        # Ensure that test directory exists
        os.makedirs(self.test_path, exist_ok=True)

        logging.info("TesterService initialized successfully.")


    def run_test(self, filename):
        """
        Execute the test for the specified Solidity file.

        :param filename: Name of the Solidity file (e.g., 'Foo.sol').
        :return: TestOutput dictionary containing status, feedback, and suggestions.
        """
        try:
            logging.info(f"Running test for file: {filename}")
            test_result = self.tester_agent.run_test(filename)
            if test_result:
                logging.info(f"Test result for {filename}: {test_result}")
            else:
                logging.warning(f"Test execution failed for {filename}.")
            return test_result
        except Exception as e:
            logging.error(f"Error running test for {filename}: {e}")
            raise e

    def get_forge_output(self):
        """
        Retrieve the Forge output from the last test run.

        :return: Forge output as a string.
        """
        return self.tester_agent.get_forge_output()
    