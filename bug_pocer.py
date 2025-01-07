import logging
import json
import os
import sys
from datetime import datetime
from argparse import ArgumentParser
from pathlib import Path
from lib.file_lib import read_file
from services.builder_service import BuilderService
from services.hacker_service import HackerService
from services.tester_service import TesterService
from lib.log_lib import setup_logging, move_log_file, log_file_differences


def load_config_and_merge(args):
    config = {}
    if args.config is not None:
        try:
            with open(args.config, "r") as f:
                config = json.load(f)
            logging.info(f"Loaded config from `{args.config}`:")
        except Exception as e:
            logging.error(f"Failed to read config file `{args.config}`: {e}")
            print(f"Could not read config file `{args.config}`. Using defaults.")

    def pick(cli_value, config_key, fallback):
        if cli_value is not None:
            return cli_value
        return config.get(config_key, fallback)

    final_settings = {}
    final_settings['builder_temp']    = pick(args.builder_temp,   'builder_temp',    1)
    final_settings['hacker_temp']     = pick(args.hacker_temp,    'hacker_temp',     1)
    final_settings['tester_temp']     = pick(args.tester_temp,    'tester_temp',     1)
    final_settings['filename']        = pick(args.filename,       'filename',        None)
    final_settings['num_attempts']    = pick(args.num_attempts,   'num_attempts',    7)
    
    final_settings['forge_bug_pocs_dir'] = pick(None, 'forge_bug_pocs_dir', None)
    final_settings['olympix_path'] = pick(None, 'olympix_path', None)

    # Log each setting
    for key, value in final_settings.items():
        logging.info("  %s = %s", key, value)

    return final_settings


def main(args):
    # Set up logging
    log_path = setup_logging()
    logging.info(f"Logging path set to: {log_path}")

    # Load config and merge with CLI arguments
    settings = load_config_and_merge(args)

    forge_bug_pocs_dir = settings['forge_bug_pocs_dir']
    if forge_bug_pocs_dir is None:
        logging.info(f"Forge project directory not configured in `{args.config}`.")
        print(f"Forge project directory not configured in `{args.config}`.")
        sys.exit(1)
        
    olympix_path = settings['olympix_path']
    if olympix_path is None:
        logging.info(f"Olympix path not configured in `{args.config}`.")
        print(f"Olympix path not configured in `{args.config}`.")
        sys.exit(1)

    logging.info(f"Forge directory being used for tests: {forge_bug_pocs_dir}")
    logging.info(f"Provided path to olympix.exe: {olympix_path}")

    src_path     = os.path.join(forge_bug_pocs_dir, "src")
    exploit_path = os.path.join(forge_bug_pocs_dir, "exploits")
    test_path    = os.path.join(forge_bug_pocs_dir, "test")

    print("Setting up builder service... ", end="")
    builder_service = BuilderService(
        forge_bug_pocs_dir,
        olympix_path,
        settings['builder_temp'],
    )
    print("Done.")
    logging.info("Setup for builder_service was successful.")

    print("Setting up hacker service... ", end="")
    hacker_service = HackerService(
        forge_bug_pocs_dir,
        settings['hacker_temp'],
    )
    print("Done.")
    logging.info("Setup for hacker_service was successful.")

    print("Setting up tester service... ", end="")
    tester_service = TesterService(
        forge_bug_pocs_dir,
        settings['tester_temp'],
    )
    print("Done.")
    logging.info("Setup for tester_service was successful.")

    # Figure out which files to target
    if settings['filename'] is not None:
        filename = settings['filename']
        if not filename.endswith('.sol'):
            logging.error(f"File `{filename}` is not a .sol file.")
            print(f"File `{filename}` is not a .sol file.")
            sys.exit(1)
        logging.info(f"Starting bug_pocer for file `{filename}`...")
        print(f"Starting `bug_pocer.py` for file `{filename}`...")
        target_files = [filename]
    else:
        logging.info("Starting bug_pocer for all .sol files...")
        print("Starting `bug_pocer.py` for all .sol files...")
        target_files = [
            f.name for f in Path(src_path).iterdir()
            if f.is_file() and f.suffix.lower() == '.sol'
        ]

    files_succeeded = []
    files_failed = []

    for file in target_files:
        test_dict = None
        status = None
        file_success = False

        exploit_filename = f"{os.path.splitext(file)[0]}Exploit.sol"
        test_filename    = f"{os.path.splitext(file)[0]}Test.sol"

        exploit_file_path = os.path.join(exploit_path, exploit_filename)
        test_file_path    = os.path.join(test_path, test_filename)

        # Retry attempts
        for attempt in range(1, settings['num_attempts'] + 1):
            logging.info(f"Starting attempt {attempt}/{settings['num_attempts']} for `{file}`")
            print("=" * 70, "\n", f"Starting attempt {attempt}/{settings['num_attempts']} for `{file}`", sep="")

            if status == 'unknown':
                logging.info("tester service returned 'unknown' status.")
                raise Exception("Tester service returned 'unknown' status.")

            if (attempt == 1 or status == 'builder_error'):
                old_builder = read_file(test_file_path)
                logging.info("Executing builder service...")
                print("Executing builder service... ", end="")
                start_time = datetime.now()
                build_dict = builder_service.generate_test(
                    file,
                    tester_service.get_forge_output(),
                    test_dict
                )
                elapsed_time = (datetime.now() - start_time).total_seconds()
                print(f"took {round(elapsed_time, 2)} seconds")
                log_file_differences(old_builder, read_file(test_file_path))

            if (attempt == 1 or status == 'hacker_failure'):
                old_hacker = read_file(exploit_file_path)
                logging.info("Executing hacker service...")
                print("Executing hacker service... ", end="")
                start_time = datetime.now()
                exploit_dict = hacker_service.generate_exploit(
                    builder_service.get_analysis_data(file),
                    file,
                    builder_service.get_test_code(file),
                    tester_service.get_forge_output(),
                    test_dict
                )
                elapsed_time = (datetime.now() - start_time).total_seconds()
                print(f"took {round(elapsed_time, 2)} seconds")
                log_file_differences(old_hacker, read_file(exploit_file_path))

            logging.info("Executing tester service...")
            print("Executing tester service... ", end="")
            start_time = datetime.now()
            test_dict = tester_service.run_test(file)
            elapsed_time = (datetime.now() - start_time).total_seconds()
            print(f"took {round(elapsed_time, 2)} seconds")

            status = test_dict['status']
            logging.info(f"Tester service returned status: {status}")
            print(f"Tester service returned status: {status}")

            if status == 'success':
                logging.info(f"{file} successfully exploited in {attempt} attempt(s)!")
                print(f"`{file}` was exploited in {attempt} attempt(s)!")
                file_success = True
                status = None
                break
            else:
                logging.info(f"Attempt {attempt} for {file} failed.")
                print(f"Attempt {attempt} for `{file}` failed.")

        if file_success:
            files_succeeded.append(file)
        else:
            files_failed.append(file)
            logging.info(f"Exhausted attempts for `{file}`, deleting test and exploit files.")
            print(f"Exhausted attempts for `{file}`")
            print("Removing failing test and exploit files... ", end="")
            if os.path.exists(exploit_file_path):
                os.remove(exploit_file_path)
                logging.info(f"Deleted exploit file: {exploit_file_path}")
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
                logging.info(f"Deleted test file: {test_file_path}")
            print("Done.")

        # Reset variables for next file
        test_dict = None
        tester_service.reset_forge_output()

    logging.info("Summary of results:")
    logging.info(f"Succeeded: {files_succeeded}")
    logging.info(f"Failed: {files_failed}")

    print("=" * 70, "\n", "Summary of Results", sep="")
    print("Succeeded:")
    if files_succeeded:
        for f in files_succeeded:
            print(f"  - {f}")
    else:
        print("  None")

    print("Failed:")
    if files_failed:
        for f in files_failed:
            print(f"  - {f}")
    else:
        print("  None")

    # Move the log file
    move_log_file(log_path, len(files_failed) == 0)
    

if __name__ == "__main__":
    parser = ArgumentParser(
        description="Bug pocer script to exploit solidity code using GPT and olympix."
    )

    parser.add_argument(
        "-c", "--config",
        type=str,
        default='config.json',
        help="Path to a JSON config file that sets defaults."
    )

    # Temperature argument: optional with default of 1
    parser.add_argument(
        "-bt", "--builder_temp",
        type=int,
        default=None,
        help="Temperature for the builder o1 model (optional)."
    )
    parser.add_argument(
        "-ht", "--hacker_temp",
        type=int,
        default=None,
        help="Temperature for the hacker o1 model (optional)."
    )
    parser.add_argument(
        "-tt", "--tester_temp",
        type=int,
        default=None,
        help="Temperature for the tester o1 model (optional)."
    )

    parser.add_argument(
        "-f", "--filename",
        type=str,
        default=None,
        help="Name of the Solidity file to exploit (optional)."
    )

    parser.add_argument(
        "-n", "--num_attempts",
        type=int,
        default=None,
        help="Number of attempts before quitting (optional)."
    )

    args = parser.parse_args()
    main(args)
