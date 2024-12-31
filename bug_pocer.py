import logging
import os
from datetime import datetime
from argparse import ArgumentParser
from pathlib import Path
from lib.file_lib import read_file
from services.builder_service import BuilderService
from services.hacker_service import HackerService
from services.tester_service import TesterService
from lib.log_lib import setup_logging, move_log_file, log_file_differences


def main(args):
    log_path = setup_logging()
    logging.info("Logging path set to: {log_path}")

    forge_bug_pocs_dir = "/mnt/c/Users/sunny/Downloads/Sunny/Olympix/Trial/bug-pocer/forge_bug_pocs"
    logging.info(f"Forge directory being used for tests: {forge_bug_pocs_dir}")

    olympix_path = '/mnt/c/Users/sunny/Downloads'
    logging.info(f"Provided path to olympix.exe: {olympix_path}")

    src_path = os.path.join(forge_bug_pocs_dir, "src")
    exploit_path = os.path.join(forge_bug_pocs_dir, "exploits")
    test_path = os.path.join(forge_bug_pocs_dir, "test")

    print(f"Setting up builder service... ", end="")
    builder_service = BuilderService(
        forge_bug_pocs_dir,
        olympix_path,
        args.builder_temp,
    )
    print("Done.")
    logging.info(f"Setup for builder_service was successful.")

    print(f"Setting up hacker service... ", end="")
    hacker_service = HackerService(
        forge_bug_pocs_dir,
        args.hacker_temp,
    )
    print("Done.")
    logging.info(f"Setup for hacker_service was successful.")

    print(f"Setting up tester service... ", end="")
    tester_service = TesterService(
        forge_bug_pocs_dir,
        args.tester_temp,
    )
    print("Done.")
    logging.info(f"Setup for tester_service was successful.")

    if args.filename is not None:
        logging.info(f"Starting bug_pocer for file `{args.filename}`...")
        print(f"Starting `bug_pocer.py` for file `{args.filename}`.")
        target_files = [args.filename]
    else:
        logging.info(f"Starting bug_pocer for all files...")
        print(f"Starting `bug_pocer.py` for all files.")
        target_files = [f.name for f in Path(src_path).iterdir() if f.is_file()]

    success = True
    for file in target_files:
        test_dict = None
        status = None

        exploit_filename = f"{os.path.splitext(file)[0]}Exploit.sol"
        test_filename = f"{os.path.splitext(file)[0]}Test.sol"

        exploit_file_path = os.path.join(exploit_path, exploit_filename)
        test_file_path = os.path.join(test_path, test_filename)

        # Execute attempt with retries
        for attempt in range(1, args.num_attempts+1):
            logging.info(f"Starting attempt {attempt}/{args.num_attempts} for {file}!")
            print("=" * 70, "\n", f"Starting attempt {attempt}/{args.num_attempts} for `{file}`", sep="")

            if status == 'unknown':
                logging.info("tester service returned 'unknown' status.")
                raise Exception("Tester service returned 'unknown' status.")

            if (attempt == 1 or status == 'builder_error'):
                old_builder = read_file(test_file_path)
                logging.info("Executing builder service...")
                print("Executing builder service... ", end="")
                start_time = datetime.now()
                build_dict = builder_service.generate_test(file,
                                                           tester_service.get_forge_output(),
                                                           test_dict)
                elapsed_time = (datetime.now() - start_time).total_seconds()
                print(f"took {round(elapsed_time, 2)} seconds")
                log_file_differences(old_builder, read_file(test_file_path))
            if (attempt == 1 or status == 'hacker_failure'):
                old_hacker = read_file(exploit_file_path)
                logging.info("Executing hacker service...")
                print("Executing hacker service... ", end="")
                start_time = datetime.now()
                exploit_dict = hacker_service.generate_exploit(builder_service.get_analysis_data(),
                                                               file,
                                                               builder_service.get_test_code(file),
                                                               tester_service.get_forge_output(),
                                                               test_dict)
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
                print(f"`{file}` was exploited in {attempt} attempt(s).")
                status = None
                break
            else:
                logging.info(f"Attempt {attempt} for {file} failed.")
                print(f"Attempt {attempt} for `{file}` failed.")
                if attempt == args.num_attempts:
                    success = False

        # Reset variables for the next file
        test_dict = None
        tester_service.reset_forge_output()

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
