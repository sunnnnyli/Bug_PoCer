import os
import logging
from typing import Optional

from agents.builder.builder_agent import BuilderAgent


class BuilderService:
    def __init__(
        self,
        project_root_path: str,
        olympix_path: str,
        temp: int = 1,
        test_skeleton_path: Optional[str] = None
    ):
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


    def generate_test(self, filename, error_data=None, test_analysis_data=None):
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
        
    def get_analysis_data(self, filename):
        try:
            return self.builder_agent.get_analysis_data(filename)
        except Exception as e:
            logging.error(f"Error retrieving analysis data for {filename}: {e}")
            raise e


    def get_test_code(self, filename):
        try:
            return self.builder_agent.get_test_code(filename)
        except Exception as e:
            logging.error(f"Error retrieving test code for {filename}: {e}")
            raise e
