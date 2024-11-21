import logging
from models.ForgeOutput import ForgeOutput
import subprocess


class ForgeLib:
    @staticmethod
    def run_forge_test(ethernaut_chal, proj_root_path) -> ForgeOutput:
        # Run `forge test` with specific challenge and capture the output
        p = subprocess.run(
            ["forge", "test", "-vvv", "--match-contract", f"Test{ethernaut_chal}Exploit"],
            cwd=proj_root_path, 
            text=True, 
            capture_output=True, 
            check=False
        )

        logging.info(f"`run_forge_test()` executing command: forge test -vvv --match-contract Test{ethernaut_chal}Exploit")

        # Return the output and return code, trimming the output to 3000 characters
        result = ForgeOutput((p.stdout + p.stderr)[:3000], p.returncode)

        if "No tests to run" in result.output_str:
            logging.error("Forge could not find forge tests to run")
            raise Exception("'forge_lib: run_forge_test()': Forge could not find tests to run.")
        
        return result
    