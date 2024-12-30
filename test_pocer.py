from datetime import datetime
from agents.builder_agent import BuilderAgent
from agents.hacker_agent import HackerAgent
from agents.tester_agent import TesterAgent
import logging
import os

def setup_logging():
    # Create 'logs' directory if it doesn't exist
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Define log filename with challenge name and timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename = f"{timestamp}.log"
    log_path = os.path.join(logs_dir, log_filename)

    # Configure logging
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format='%(message)s'
    )
    logging.info("Logging setup complete...")
    logging.info(f"Initial log file path: {log_path}")
    return log_path

forge_path = '/mnt/c/Users/sunny/Downloads/Sunny/Olympix/Trial/bug-pocer/forge_bug_pocs'
olympix_path = '/mnt/c/Users/sunny/Downloads'

setup_logging()
filename = 'FrontRunningVulnerable.sol'

builder = BuilderAgent('o1', forge_path, olympix_path, 1, None)
hacker = HackerAgent('o1', forge_path, 1, None)
tester = TesterAgent('o1', forge_path, 1)

build_dict = builder.generate_test(filename)
hack_dict = hacker.exploit(builder.get_analysis_data(), filename, builder.get_test_code(filename))
test_dict = tester.run_test(filename)

test_output = tester.get_forge_output()
print(test_dict)
print(test_output)
