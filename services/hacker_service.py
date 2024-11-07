import os
import logging
from agents.hacker_agent import HackerAgent
from forge_lib import ForgeLib

class HackerService:
    def __init__(self, project_root_path, ethernaut_challenge, hacker_temp):
        self.project_root_path = project_root_path
        self.ethernaut_challenge = ethernaut_challenge
        self.hacker_temp = hacker_temp
        self.attempt_count = 0

        self.contract_folder = os.path.join(self.project_root_path, "exploits", ethernaut_challenge)
        self.test_folder = os.path.join(self.project_root_path, "test")
        self.source_folder = os.path.join(self.project_root_path, "src", ethernaut_challenge)

        # Load exploit resources
        self.exploit_contract_path = os.path.join(self.contract_folder, f"{ethernaut_challenge}ExploitAttempt.sol")
        self.exploit_contract_skeleton = self.load_file(self.contract_folder, f"{ethernaut_challenge}ExploitSkeleton.sol")

        # Load source contract and tests
        self.test_case_skeleton = self.load_file(self.test_folder, f"Test{ethernaut_challenge}Exploit.sol")
        self.victim_sol_content = self.load_file(self.source_folder, f"{ethernaut_challenge}.sol")

        # Initialize the hacker agent
        self.hacker_agent = HackerAgent(
            self.victim_sol_content, 
            self.exploit_contract_skeleton,
            self.test_case_skeleton
        )

    def load_file(self, folder, file_name):
        """Helper to read file content from the exploits folder."""
        filepath = os.path.join(folder, file_name)
        with open(filepath, "r") as file:
            return file.read()
        
    """Run attempt to exploit the challenge and continue reattempting until the exploit is successful."""
    def execute(self, attempts=3):
        curr_attempts = 0
        while curr_attempts < attempts:
            logging.info(f"Attempt {curr_attempts} for challenge {self.ethernaut_challenge}")
            
            if curr_attempts == 0:
                hacker_output, prompt = self.hacker_agent.attempt()
            else:
                # On subsequent attempts, use the previous forge output for a new attempt
                hacker_output, prompt = self.hacker_agent.attempt(forge_output.output_str)
            
            # Log the formatted prompt fed into the AI model
            logging.info(f"Prompt Fed to AI Model:\n{prompt}")

            self.hacker_agent.write_exploit(hacker_output.solidity_attempt, self.exploit_contract_path)
            logging.info(f"Generated Exploit Code{' (Reattempt)' if curr_attempts > 0 else ''}:\n{hacker_output.solidity_attempt}")

            # Run forge test and capture output
            forge_output = ForgeLib.run_forge_test(self.ethernaut_challenge, self.project_root_path)

            print(f"Attempt {curr_attempts}:")
            print("=" * 70)

            # Check if the test succeeded
            if forge_output.return_code == 0:
                logging.info(f"Successful exploit for challenge {self.ethernaut_challenge} on attempt {curr_attempts}")
                logging.info(f"Forge Output: {forge_output.output_str}")
                print(f"Output:\n{forge_output.output_str}\nSuccessfully exploited the challenge!")
                print("=" * 70)
                break
            else:
                logging.warning(f"Attempt {curr_attempts} failed for challenge {self.ethernaut_challenge}")
                logging.warning(f"Forge Output: {forge_output.output_str}")
                print(f"Output:\n{forge_output.output_str}\nForge test failed.")
                print("=" * 70, "\n")

            curr_attempts += 1

        logging.info(f"Total attempts: {curr_attempts}")
