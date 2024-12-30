import logging
import os
from datetime import datetime
from argparse import ArgumentParser
from services.tester_service import TesterService
from services.hacker_service import HackerService


def setup_logging(filename):
    # Create 'logs' directory if it doesn't exist
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Define log filename with challenge name and timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename = f"{timestamp}_{filename}.log"
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
    log_path = setup_logging(args.filename)
    if args.filename is not None:
        logging.info(f"Starting bug_pocer for file `{args.filename}`")
    else:
        logging.info(f"No specific file given, starting bug_pocer for all files.")

    forge_bug_pocs_dir = "/mnt/c/Users/sunny/Downloads/Sunny/Olympix/Trial/bug-pocer/forge_bug_pocs"
    logging.info(f"Forge directory being used for tests: {forge_bug_pocs_dir}")

    olympix_path = '/mnt/c/Users/sunny/Downloads'
    logging.info(f"Provided path to olympix.exe: {olympix_path}")

    # Initialize TesterService and pass the paths
    tester_service = TesterService(
        forge_bug_pocs_dir,
        olympix_path,
        args.hacker_temp,
    )
    logging.info(f"Setup for hacker_service was successful.")

    # Initialize HackerService (manages exploit attempts) and pass the analysis
    hacker_service = HackerService(
        forge_bug_pocs_dir,
        olympix_path,
        args.hacker_temp,
    )
    logging.info(f"Setup for hacker_service was successful.")

    # Execute attempt with retries
    logging.info(f"Executing hacker_service...")
    exploit_status = hacker_service.execute(args.num_attempts)

    # Move the log file based on the exploit status
    move_log_file(log_path, exploit_status)
    

if __name__ == "__main__":
    parser = ArgumentParser(
        description="Bug pocer script to exploit solidity code using the gpt o1 model and olympix static analysis."
    )

    # Temperature argument: optional with default of 1
    parser.add_argument(
        "-t", "--hacker_temp",
        type=float,
        default=1,
        help="Temperature for the o1 model (optional, defaults to 1)."
    )

    # Filename argument: optional with a default of None
    parser.add_argument(
        "-f", "--filename",
        type=str,
        default=None,
        help="Name of the Solidity file to exploit (optional, defaults to None)."
    )

    # Number of attempts: optional with default of 7
    parser.add_argument(
        "-n", "--num_attempts",
        type=int,
        default=7,
        help="Number of attempts before quitting (optional, defaults to 7)."
    )

    args = parser.parse_args()
    main(args)
