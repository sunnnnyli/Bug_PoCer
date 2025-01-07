import logging
import os
import subprocess

class ForgeOutput:
    def __init__(self, output_str, return_code):
        self.output_str = output_str
        self.return_code = return_code

class ForgeLib:
    @staticmethod
    def run_forge_test(proj_root_path, filename: str) -> ForgeOutput:
        # Run `forge test` with specific filename and capture the output
        file_base_name = os.path.splitext(filename)[0]
        p = subprocess.run(
            ["forge", "test", "-vvv", "--match-contract", file_base_name],
            cwd=proj_root_path, 
            text=True, 
            capture_output=True, 
            check=False
        )

        logging.info(f"`run_forge_test()` executing command: forge test -vvv --match-contract {file_base_name}")

        # Return the output and return code, trimming the output to 4000 characters starting from the end
        result = ForgeOutput((p.stdout + p.stderr)[-4000:], p.returncode)

        if "No tests to run" in result.output_str:
            logging.error("Forge could not find tests to run!")
            raise Exception("'forge_lib.py: run_forge_test()': Forge could not find tests to run.")
        
        return result
    