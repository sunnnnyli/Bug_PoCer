import difflib
import logging
import os
from datetime import datetime
from argparse import ArgumentParser
from pathlib import Path
from services.builder_service import BuilderService
from services.hacker_service import HackerService
from services.tester_service import TesterService


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
        format='%(message)s'
    )
    logging.info("[bug_pocer.py] Logging path set to: {log_path}")
    return log_path


def log_file_differences(old_content, new_content):
    try:
        # Compute differences
        diff = difflib.unified_diff(
            old_content,
            new_content,
            fromfile='Previous Exploit File',
            tofile='Current Exploit File',
            lineterm=''
        )

        difference = '\n'.join(diff)

        # Log the differences
        logging.info("[bug_pocer.py] Differences between previous and current exploit file:\n%s", difference)

        return difference
    except FileNotFoundError as e:
        logging.warning(f"[bug_pocer.py] File not found for comparison: {e}")
    except Exception as e:
        logging.error(f"[bug_pocer.py] Error while logging file differences: {e}")


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
    logging.info(f"[bug_pocer.py] Log file moved to: {target_path}")
    print(f"Log file stored in: {target_path}")


def main(args):
    log_path = setup_logging()

    forge_bug_pocs_dir = "/mnt/c/Users/sunny/Downloads/Sunny/Olympix/Trial/bug-pocer/forge_bug_pocs"
    logging.info(f"[bug_pocer.py] Forge directory being used for tests: {forge_bug_pocs_dir}")

    olympix_path = '/mnt/c/Users/sunny/Downloads'
    logging.info(f"[bug_pocer.py] Provided path to olympix.exe: {olympix_path}")

    src_path = os.path.join(forge_bug_pocs_dir, "src")

    print(f"Setting up builder service... ", end="")
    builder_service = BuilderService(
        forge_bug_pocs_dir,
        olympix_path,
        args.builder_temp,
    )
    print("Done.")
    logging.info(f"[bug_pocer.py] Setup for builder_service was successful.")

    print(f"Setting up hacker service... ", end="")
    hacker_service = HackerService(
        forge_bug_pocs_dir,
        args.hacker_temp,
    )
    print("Done.")
    logging.info(f"[bug_pocer.py] Setup for hacker_service was successful.")

    print(f"Setting up tester service... ", end="")
    tester_service = TesterService(
        forge_bug_pocs_dir,
        args.tester_temp,
    )
    print("Done.")
    logging.info(f"[bug_pocer.py] Setup for tester_service was successful.")

    if args.filename is not None:
        logging.info(f"[bug_pocer.py] Starting bug_pocer for file `{args.filename}`...")
        print(f"Starting `bug_pocer.py` for file `{args.filename}`.")
        target_files = [args.filename]
    else:
        logging.info(f"[bug_pocer.py] Starting bug_pocer for all files...")
        print(f"Starting `bug_pocer.py` for all files.")
        target_files = [f.name for f in Path(src_path).iterdir() if f.is_file()]

    success = True
    for file in target_files:
        test_dict = None
        status = None

        # Execute attempt with retries
        for attempt in range(1, args.num_attempts+1):
            logging.info(f"[bug_pocer.py] Starting attempt {attempt} for {file}!")
            print("=" * 70, "\n", f"Starting attempt {attempt} for `{file}`", sep="")

            if status == 'unknown':
                logging.info("[bug_pocer.py] tester service returned 'unknown' status.")
                raise Exception("Tester service returned 'unknown' status.")

            if (attempt == 1 or status == 'builder_error'):
                logging.info("[bug_pocer.py] Executing builder service...")
                print("Executing builder service...")
                build_dict = builder_service.generate_test(file,
                                                           tester_service.get_forge_output(),
                                                           test_dict)
            if (attempt == 1 or status == 'hacker_failure'):
                logging.info("[bug_pocer.py] Executing hacker service...")
                print("Executing hacker service...")
                exploit_dict = hacker_service.generate_exploit(builder_service.get_analysis_data(),
                                                               file,
                                                               builder_service.get_test_code(file),
                                                               tester_service.get_forge_output(),
                                                               test_dict)

            logging.info("[bug_pocer.py] Executing tester service...")
            print("Executing tester service...")
            test_dict = tester_service.run_test(file)

            status = test_dict['status']
            logging.info(f"[bug_pocer.py] Tester service returned status: {status}")
            print(f"Tester service returned status: {status}")
            
            if status == 'success':
                logging.info(f"[bug_pocer.py] Source code successfully exploited in {attempt} attempt(s)!")
                print(f"Your source code was exploited in {attempt} attempt(s).")
                status = None
                break
            else:
                logging.info(f"[bug_pocer.py] Attempt {attempt} for {file} failed.")
                print(f"Attempt {attempt} for `{file}` failed.")
                if attempt == args.num_attempts:
                    success = False

    # Move the log file based on the build and hack status
    move_log_file(log_path, success)
    

if __name__ == "__main__":
    parser = ArgumentParser(
        description="Bug pocer script to exploit solidity code using the gpt o1 model and olympix static analysis."
    )

    # Temperature argument: optional with default of 1
    parser.add_argument(
        "-bt", "--builder_temp",
        type=int,
        default=1,
        help="Temperature for the builder o1 model (optional, defaults to 1)."
    )
    parser.add_argument(
        "-ht", "--hacker_temp",
        type=int,
        default=1,
        help="Temperature for the hacker o1 model (optional, defaults to 1)."
    )
    parser.add_argument(
        "-tt", "--tester_temp",
        type=int,
        default=1,
        help="Temperature for the tester o1 model (optional, defaults to 1)."
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
