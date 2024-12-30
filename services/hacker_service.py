import os
import logging
import difflib
from datetime import datetime
from agents.hacker_agent import HackerAgent
from agents.tester_agent import TesterAgent
from forge_lib import ForgeLib
from file_lib import write_file, read_file


class HackerService:
    def __init__(self, project_root_path, olympix_path, temp=1):
        self.project_root_path = project_root_path
        self.olympix_path = olympix_path
        self.temp = temp
        self.attempt_count = 0

        self.exploit_folder = os.path.join(self.project_root_path, "exploits")
        self.test_folder = os.path.join(self.project_root_path, "test")
        self.source_folder = os.path.join(self.project_root_path, "src")

        # Load exploit resources
        self.exploit_contract_path = os.path.join(self.contract_folder, f"{ethernaut_challenge}ExploitAttempt.sol")
        self.exploit_contract_skeleton = read_file(self.contract_folder, f"{ethernaut_challenge}ExploitSkeleton.sol")

        # Load source contract and tests
        self.test_case_skeleton = read_file(self.test_folder, f"Test{ethernaut_challenge}Exploit.sol")
        self.victim_sol_content = read_file(self.source_folder, f"{ethernaut_challenge}.sol")

        # Initialize agents
        self.hacker_agent = HackerAgent('o1', self.project_root_path)
        self.tester_agent = TesterAgent('o1', self.project_root_path, olympix_path)


    def log_file_differences(self, old_file_path, new_content):
        try:
            with open(old_file_path, 'r') as old_file:
                old_content = old_file.read().splitlines() 

            # Compute differences
            diff = difflib.unified_diff(
                old_content,
                new_content.splitlines(),
                fromfile='Previous Exploit File',
                tofile='Current Exploit File',
                lineterm=''
            )

            difference = '\n'.join(diff)

            # Log the differences
            logging.info("Differences between previous and current exploit file:\n%s", difference)

            return difference
        except FileNotFoundError as e:
            logging.warning(f"File not found for comparison: {e}")
        except Exception as e:
            logging.error(f"Error while logging file differences: {e}")
        

    """Run attempt to exploit the challenge and continue reattempting until the exploit is successful."""
    def execute(self, attempts) -> bool:
        curr_attempts = 0
        forge_output = None

        while curr_attempts < attempts:
            print(f"Attempt {curr_attempts}:")
            print("=" * 10)
            logging.info(f"Starting attempt {curr_attempts} for challenge {self.ethernaut_challenge}")
            
            print("Generating exploit code...")
            start_time = datetime.now()

            if curr_attempts == 0:
                hacker_output = self.hacker_agent.attempt()
            else:
                # On subsequent attempts, use the previous forge output for a new attempt
                hacker_output = self.hacker_agent.attempt(forge_output.output_str)

            difference = (datetime.now() - start_time).total_seconds()
            print(f"Done... (took {difference} seconds)")
            
            logging.info(f"AI generated exploit code{' (reattempt)' if curr_attempts > 0 else ''}:\n{hacker_output.solidity_attempt}")
            
            if curr_attempts > 0:
                self.log_file_differences(self.exploit_contract_path, hacker_output.solidity_attempt)

            print("Writing to exploit file...")
            self.hacker_agent.write_exploit(hacker_output.solidity_attempt, self.exploit_contract_path)
            with open(self.exploit_contract_path, "r") as file:
                logging.info(f"Content of file `{self.exploit_contract_path}`:\n{file.read()}")
            print("Done...")

            # Run forge test and capture output
            print("Testing exploit code...")
            forge_output = ForgeLib.run_forge_test(self.ethernaut_challenge, self.project_root_path)
            print("Done...")
            print(f"Forge Output:\n{forge_output.output_str}\n")

            # Check if the test succeeded
            if forge_output.return_code == 0:
                logging.info(f"Successful exploit for challenge {self.ethernaut_challenge} on attempt {curr_attempts}")
                logging.info(f"Forge Output:\n{forge_output.output_str}")
                print("Successfully exploited the challenge!")
                print("=" * 70, "\n")
                curr_attempts += 1
                break
            else:
                logging.warning(f"Attempt {curr_attempts} failed for challenge {self.ethernaut_challenge}")
                logging.warning(f"Forge Output:\n{forge_output.output_str}")
                print("Forge test failed. More information can be found in logs.")
                print("=" * 70, "\n")
                curr_attempts += 1
            
        status = "***SUCCESS***" if forge_output.return_code == 0 else "***FAILURE***"
        logging.info(f"Exploit status: {status} after {curr_attempts} attempt{'s' if curr_attempts > 1 else ''}")
        return forge_output.return_code == 0
