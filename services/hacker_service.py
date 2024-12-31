import os
import logging
from typing import Optional
from agents.hacker_agent import HackerAgent


class HackerService:
    def __init__(
            self,
            project_root_path: str,
            temp: int = 1,
            exploit_skeleton_path: Optional[str] = None
        ):
        self.project_root_path = project_root_path
        self.exploit_folder = os.path.join(self.project_root_path, "exploits")
        self.test_folder = os.path.join(self.project_root_path, "test")
        self.source_folder = os.path.join(self.project_root_path, "src")

        self.hacker_agent = HackerAgent(
            gpt_model='o1',
            forge_path=project_root_path,
            temp=temp,
            exploit_skeleton_path=exploit_skeleton_path
        )


    def generate_exploit(self, static_analysis, filename, test_code, forge_output=None, exploit_analysis_data=None):
        try:
            logging.info(f"Generating exploit for file: {filename}")
            exploit = self.hacker_agent.exploit(
                static_analysis=static_analysis,
                filename=filename,
                test_code=test_code,
                forge_output=forge_output,
                exploit_analysis_data=exploit_analysis_data
            )
            logging.info(f"Done...")
            return exploit
        except Exception as e:
            logging.error(f"Error generating exploit for {filename}: {e}")
            raise e

    def get_exploit_code(self, filename):
        try:
            return self.hacker_agent.get_exploit_code(filename)
        except Exception as e:
            logging.error(f"Error retrieving exploit code for {filename}: {e}")
            raise e
        