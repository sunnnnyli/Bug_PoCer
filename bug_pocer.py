import logging
import os
from datetime import datetime
from argparse import ArgumentParser
from services.hacker_service import HackerService


def setup_logging(challenge_name):
    # Create 'logs' directory if it doesn't exist
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Define log filename with challenge name and timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename = f"{timestamp}_{challenge_name}.log"
    log_path = os.path.join(logs_dir, log_filename)

    # Configure logging
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s'
    )
    logging.info("Logging setup complete...")
    logging.info(f"Initial log file path: {log_path}")
    return log_path


def move_log_file(log_path, exploit_status):
    # Determine success or failure and set the target directory
    if exploit_status:
        target_dir = os.path.join('logs', 'Successes')
    else:
        target_dir = os.path.join('logs', 'Failures')

    # Create the target directory if it doesn't exist
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # Move the log file
    target_path = os.path.join(target_dir, os.path.basename(log_path))
    os.rename(log_path, target_path)
    logging.info(f"Log file was moved based on exploit status. New log file path: {target_path}")
    print(f"Log file stored in: {target_path}")


def main(args):
    log_path = setup_logging(args.chal)
    logging.info(f"Starting bug_pocer for challenge: {args.chal}")

    forge_bug_pocs_dir = "/mnt/c/Users/sunny/Downloads/Sunny/Olympix/bug_pocer/forge_bug_pocs"
    logging.info(f"Forge directory being used for tests: {forge_bug_pocs_dir}")

    # Initialize HackerService (manages exploit attempts)
    hacker_service = HackerService(
        forge_bug_pocs_dir,
        args.chal,
        args.hacker_temp,
    )
    logging.info(f"Setup for hacker_service was successful.")

    # Execute attempt with retries
    logging.info(f"Executing hacker_service...")
    exploit_status = hacker_service.execute()

    # Move the log file based on the exploit status
    move_log_file(log_path, exploit_status)
    

if __name__ == "__main__":
    parser = ArgumentParser(description="Bug pocer script to exploit Ethernaut challenges using the o1-mini model.")
    parser.add_argument("--chal", help="The name of the Ethernaut challenge to exploit.", required=True)
    parser.add_argument("--hacker_temp", type=float, help="Temperature for the o1-mini model.", default=1)
    
    args = parser.parse_args()
    main(args)
