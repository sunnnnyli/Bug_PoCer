import logging
import os
from datetime import datetime
import difflib


def setup_logging():
    # Create 'logs' directory if it doesn't exist
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Define log filename with timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename = f"{timestamp}.log"
    log_path = os.path.join(logs_dir, log_filename)

    # Configure logging
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format='[%(filename)s:%(funcName)s] %(message)s'
    )
    return log_path


def log_file_differences(old_content: str, new_content: str):
    try:
        # Split the strings into lists of lines
        old_content_lines = old_content.splitlines()
        new_content_lines = new_content.splitlines()

        # Compute differences
        diff = difflib.unified_diff(
            old_content_lines,
            new_content_lines,
            fromfile='Previous File',
            tofile='Current File',
            lineterm=''
        )

        difference = '\n'.join(diff)

        # Log the differences
        logging.info(f"Changes made to file:\n{difference}")

        return difference
    except FileNotFoundError as e:
        logging.warning(f"File not found for comparison: {e}")
    except Exception as e:
        logging.error(f"Error while logging file differences: {e}")


def move_log_file(log_path, success: bool):
    # Determine success or failure and set the target directory
    if success:
        target_dir = os.path.join('logs', 'Successes')
    else:
        target_dir = os.path.join('logs', 'Failures')

    # Create the target directory if it doesn't exist
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # Move the log file
    target_path = os.path.join(target_dir, os.path.basename(log_path))
    os.rename(log_path, target_path)
    
    logging.info(f"Log file moved to: {target_path}")
    print(f"Log file stored in: {target_path}")
    