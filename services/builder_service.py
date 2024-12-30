import os
import logging
from typing import Optional

from agents.builder_agent import BuilderAgent


class BuilderService:
    def __init__(
        self,
        project_root_path: str,
        olympix_path: str,
        temp: int = 1,
        test_skeleton_path: Optional[str] = None
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
        self.src_path = os.path.join(self.project_root_path, "src")
        self.test_path = os.path.join(self.project_root_path, "test")
        self.exploit_path = os.path.join(self.project_root_path, "exploits")

        self.builder_agent = BuilderAgent(
            gpt_model='o1',
            forge_path=project_root_path,
            olympix_path=olympix_path,
            temp=temp,
            test_skeleton_path=test_skeleton_path
        )

        logging.info("BuilderService initialized successfully.")


    def generate_test(self, filename, error_data=None, test_analysis_data=None):
        """
        Generate a test contract for the specified Solidity file.

        :param filename: Name of the Solidity file (e.g., 'Foo.sol').
        :param error_data: (Optional) Additional error data for regeneration.
        :param test_analysis_data: (Optional) Additional analysis data.
        :return: Dictionary containing the test filename and generated test code.
        """
        try:
            if error_data is None:
                logging.info(f"Generating test for file: {filename}")
            else:
                logging.info(f"Regenerating test for file: {filename}")
            test = self.builder_agent.generate_test(filename, error_data, test_analysis_data)
            logging.info(f"Done...")
            return test
        except Exception as e:
            logging.error(f"Error generating test for {filename}: {e}")
            raise e
        
    def get_analysis_data(self):
        try:
            return self.builder_agent.get_analysis_data()
        except Exception as e:
            logging.error(f"Error retrieving analysis data: {e}")
            raise e


    def get_test_code(self, filename):
        """
        Retrieve the generated test code for a specific Solidity file.

        :param filename: Name of the Solidity file (e.g., 'Foo.sol').
        :return: Test contract code as a string.
        """
        try:
            return self.builder_agent.get_test_code(filename)
        except Exception as e:
            logging.error(f"Error retrieving test code for {filename}: {e}")
            raise e
