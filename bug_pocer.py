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
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f"{challenge_name}_{timestamp}.log"
    log_path = os.path.join(logs_dir, log_filename)

    # Configure logging
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.info("Logging setup complete.")
    return log_path

def main(args):
    log_path = setup_logging(args.chal)
    logging.info(f"Starting bug_pocer for challenge: {args.chal}")

    # proj_path = "/mnt/c/Users/sunny/Downloads/Sunny/Olympix/sunny_pocer"
    forge_bug_pocs_dir = "/mnt/c/Users/sunny/Downloads/Sunny/Olympix/sunny_pocer/forge_bug_pocs"

    # Initialize HackerService (manages exploit attempts)
    hacker_service = HackerService(
        forge_bug_pocs_dir,
        args.chal,
        args.hacker_temp,
    )

    # Execute attempt with retries
    hacker_service.execute()
    
    logging.info(f"Logging stored in {log_path}")

if __name__ == "__main__":
    parser = ArgumentParser(description="Bug pocer script to exploit Ethernaut challenges using the o1-mini model.")
    parser.add_argument("--chal", help="The name of the Ethernaut challenge to exploit.", required=True)
    parser.add_argument("--hacker_temp", type=float, help="Temperature for the o1-mini model.", default=1)
    
    args = parser.parse_args()
    main(args)
