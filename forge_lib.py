import os
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
        # Return the output and return code, trimming the output to 3000 characters
        return ForgeOutput((p.stdout + p.stderr)[:3000], p.returncode)
