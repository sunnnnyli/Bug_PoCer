import json
import logging
import os
import re
from datetime import datetime
import subprocess
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from typing_extensions import Annotated, TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from agents.builder.prompts.generation import generation
from agents.builder.prompts.regeneration import regeneration
from agents.builder.prompts.skeleton_generation import skeleton_generation
from agents.builder.prompts.skeleton_regeneration import skeleton_regeneration
from agents.builder.prompts.chained_call import chained_call
from lib.file_lib import write_file, read_file


class BuildOutput(TypedDict):
    my_test_code: Annotated[str, ..., "Your generated test contract code"]
    my_explanation: Annotated[str, ..., "Explanation of your test logic"]


class BuilderAgent:
    def __init__(self,
                 gpt_model,
                 forge_path,
                 olympix_path,
                 temp,
                 test_skeleton_path,
                 precomputed_analysis_data: dict = None,
                 precomputed_bug_map: dict = None
        ):
        self.forge_path = forge_path
        self.src_path = os.path.join(forge_path, "src")
        self.test_path = os.path.join(forge_path, "test")
        self.test_skeleton = read_file(test_skeleton_path)
        self.id = str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S_'))
        self.imported_files_cache = {}
        self.generated_tests = {}
        

        if precomputed_analysis_data is not None:
            self.analysis_data = precomputed_analysis_data
            logging.info("Using precomputed analysis data.")
        else:
            self.analysis_data = self.olympix_static_analysis(olympix_path, self.src_path)

        if precomputed_bug_map is not None:
            self.file_bug_map = precomputed_bug_map
            logging.info("Using precomputed bug map.")
        else:
            self.file_bug_map = self.build_file_bug_map(self.analysis_data)

        self.ai_model = ChatOpenAI(
            model=gpt_model,
            temperature=temp,
            openai_api_key=os.environ["OPENAI_API_KEY"]
        )

        self.chained_model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=os.environ["OPENAI_API_KEY"]
        ).with_structured_output(BuildOutput)

        # Build a workflow graph for the AI calls
        self.workflow = StateGraph(state_schema=MessagesState)
        
        def call_model(state: MessagesState):
            response = self.ai_model.invoke(state["messages"])
            return {"messages": response}
        
        self.workflow.add_edge(START, "model")
        self.workflow.add_node("model", call_model)

        memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=memory)

    def olympix_static_analysis(self, olympix_path: str, working_dir: str) -> str:
        def parse_olympix_output(stdout: str) -> dict:
            start = stdout.find('{')
            end = stdout.rfind('}')

            if start == -1 or end == -1 or end < start:
                raise ValueError("Could not find a valid JSON block in Olympix output.")

            json_str = stdout[start:end + 1]

            logging.debug(f"Extracted JSON portion:\n{json_str}")

            return json.loads(json_str)
        
        full_olympix_path = os.path.join(olympix_path, "olympix.exe")

        cmd = [
            full_olympix_path,
            "analyze",
            "-w",
            ".",
            "--output-format",
            "json"
        ]

        try:
            logging.info(f"Running olympix analysis command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=working_dir
            )

            if result.returncode != 0:
                logging.error(f"Olympix analysis failed: {result.stderr.strip()}")
                raise RuntimeError(
                    f"Olympix analysis command exited with code {result.returncode}."
                )

            logging.info(f"Olympix analysis completed successfully:\n{result.stdout}")

            analysis_data = parse_olympix_output(result.stdout)

            return analysis_data

        except FileNotFoundError as e:
            error_msg = (f"Could not locate olympix.exe at '{full_olympix_path}'.")
            logging.error(error_msg)
            raise FileNotFoundError(error_msg) from e
        except json.JSONDecodeError as e:
            logging.error(f"Could not decode JSON from Olympix output: {result.stdout}")
            raise e
        except Exception as e:
            logging.error(f"Unexpected error while running olympix.exe: {e}")
            raise


    def build_file_bug_map(self, analysis_data: dict) -> dict:
        """
        Build a quick-lookup dictionary mapping each .sol filename to a list of its bugs.
        """
        file_bug_map = {}
        files_info = analysis_data.get("files", [])

        for file in files_info:
            path = file.get("path", "")
            standardized_path = path.replace("\\", "/")

            # Extract just the final filename
            filename_only = standardized_path.split("/")[-1]

            file_bug_map[filename_only] = file.get("bugs", [])

        return file_bug_map


    def get_bugs_for_file(self, filename: str) -> list:
        if not filename.endswith(".sol"):
            filename += ".sol"
        return self.file_bug_map.get(filename, [])
    

    def find_imported_files(self, file_content: str, current_dir: str) -> dict:
        imported_contents = {}

        pattern = r'^\s*import\s+(?:\{[^}]+\}\s+from\s+)?(?:"|\')(.*?\.sol)(?:"|\')\s*;'
        matches = re.findall(pattern, file_content, flags=re.MULTILINE)

        for import_path in matches:
            # Attempt to find the absolute path
            # Handle '.' or './'
            norm_path = import_path.replace('"', '').replace("'", "")
            norm_path = norm_path.replace("./", "")
            
            # We expect these imported files to be relative to `current_dir`
            abs_import_path = os.path.join(current_dir, norm_path)
            
            # Standardize the filename only for dictionary key
            # E.g. MyLib.sol
            filename_only = os.path.basename(abs_import_path)

            if filename_only not in self.imported_files_cache:
                # If we haven't yet cached it, read the file
                if os.path.exists(abs_import_path):
                    file_data = read_file(abs_import_path)
                    self.imported_files_cache[filename_only] = file_data

                    # Recursively parse further imports from that file
                    deeper_imports = self.find_imported_files(file_data, os.path.dirname(abs_import_path))
                    imported_contents.update(deeper_imports)
                else:
                    logging.warning(f"Imported file not found on disk: {abs_import_path}")
                    self.imported_files_cache[filename_only] = f"// Could not find {filename_only}"
            
            # Once it's in the cache, add it to the local dictionary
            imported_contents[filename_only] = self.imported_files_cache[filename_only]

        return imported_contents
    

    def generate_test_for_file(self,
                               filename: str,
                               error_data: str = None,
                               test_analysis_data: dict = None) -> dict:
        # Ensure it ends with .sol
        if not filename.endswith(".sol"):
            filename += ".sol"

        # Confirm the file exists
        all_filenames = [f for f in os.listdir(self.src_path) if f.endswith(".sol")]
        if filename not in all_filenames:
            raise FileNotFoundError(f"File '{filename}' not found in the src folder.")

        file_path = os.path.join(self.src_path, filename)
        source_code = read_file(file_path)
        logging.info(f"Content read from {file_path}")

        # Grab only the relevant bugs for this file
        relevant_bugs = self.get_bugs_for_file(filename)
        relevant_bugs_str = json.dumps(relevant_bugs, indent=2)
        logging.info(f"Relevant Olympix bugs for {filename}:\n{relevant_bugs_str}")

        imported_files_dict = self.find_imported_files(source_code, self.src_path)
        
        # Construct an optional string to include imported code in the prompt
        # If we have any imports found, we attach them
        imported_code_str = ""
        if imported_files_dict:
            appended_imports = []
            for file, code in imported_files_dict.items():
                appended_imports.append(f"\n// Begin import {file}\n{code}\n// End import {file}\n")
            imported_code_str = "\n".join(appended_imports)

        # Construct the test file path
        test_filename = f"{os.path.splitext(filename)[0]}Test.sol"
        test_file_path = os.path.join(self.test_path, test_filename)

        # Determine the prompt
        if self.test_skeleton is not None:
            template = skeleton_regeneration if error_data else skeleton_generation
            format_args = {
                'source_code': source_code,
                'analysis_data': relevant_bugs_str,
                'filename': os.path.splitext(filename)[0],
                'test_skeleton': self.test_skeleton
            }
        else:
            template = regeneration if error_data else generation
            format_args = {
                'source_code': source_code,
                'analysis_data': relevant_bugs_str,
                'filename': os.path.splitext(filename)[0]
            }

        # Add 'error_data' to format arguments if it exists
        if error_data is not None:
            format_args['error_data'] = error_data
            format_args['test_analysis'] = test_analysis_data

        if imported_code_str.strip():
            format_args['import_data'] = imported_code_str
        else:
            format_args['import_data'] = "No import data"

        # Format the prompt using the selected template and arguments
        prompt = template.format(**format_args)
        logging.info(f"Prompt fed to builder agent:\n{prompt}")

        input_messages = [HumanMessage(prompt)]
        config = {"configurable": {"thread_id": self.id}}

        # Call the first AI model
        logging.info("Invoking builder agent...")
        output = self.app.invoke({"messages": input_messages}, config)
        logging.info("Builder agent returned a response.")

        # Use the second model to parse structured JSON
        try:
            o1_json_response = output["messages"][-1].content
            chained_prompt = chained_call.format(ai_response=o1_json_response)

            logging.info(f"Prompt fed to builder agent's chained model:\n{chained_prompt}")

            output_dict = self.chained_model.invoke(chained_prompt)
            logging.info("Builder agent's chained model returned a response.")

            test_code = output_dict['my_test_code']
            # explanation = output_dict['my_explanation']
        except Exception as e:
            logging.error(f"Could not parse test code from model output. Error: {e}")
            raise

        # Write the new test contract
        write_file(test_code, test_file_path)
        if error_data is None:
            logging.info(f"Created test file: {test_file_path}")
        else:
            logging.info(f"Modified test file: {test_file_path}")

        # Update our in-memory dictionary
        self.generated_tests[test_filename] = test_code
        
        # Return a dictionary with this file’s new test code
        return {test_filename: test_code}


    def generate_test(self,
                      target_file: str,
                      error_data: str = None,
                      test_analysis_data: dict = None) -> dict:
        if error_data is None:
            logging.info(f"Generating test for file: {target_file}")
        else:
            logging.info(f"Regenerating test for file: {target_file}")

        result = self.generate_test_for_file(target_file, error_data, test_analysis_data)

        logging.info("Done...")

        return result

    def get_analysis_data(self, filename) -> dict:
        relevant_bugs = self.get_bugs_for_file(filename)
        relevant_bugs_str = json.dumps(relevant_bugs, indent=2)

        return relevant_bugs_str

    def get_test_code(self, filename: str) -> str:
        test_filename = f"{os.path.splitext(filename)[0]}Test.sol"

        # Check in-memory dictionary first
        if test_filename in self.generated_tests:
            return self.generated_tests[test_filename]

        # Otherwise, fall back to reading from disk
        test_file_path = os.path.join(self.test_path, test_filename)
        if not os.path.isfile(test_file_path):
            error = f"Test file '{test_file_path}' not found in memory or on disk."
            logging.error(error)
            raise FileNotFoundError(error)

        try:
            code_from_disk = read_file(test_file_path)
            return code_from_disk
        except IOError as e:
            error = f"Failed to read the test file '{test_file_path}'. Error: {e}"
            logging.error(error)
            raise e
