import logging
import os
from datetime import datetime
import subprocess
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from typing_extensions import Annotated, TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from prompts.builder.generation import generation
from prompts.builder.regeneration import regeneration
from prompts.builder.skeleton_generation import skeleton_generation
from prompts.builder.skeleton_regeneration import skeleton_regeneration
from prompts.builder.chained_call import chained_call
from file_lib import write_file, read_file


class BuildOutput(TypedDict):
    my_test_code: Annotated[str, ..., "Your generated test contract code"]
    my_explanation: Annotated[str, ..., "Explanation of your test logic"]


class BuilderAgent:
    def __init__(self, gpt_model, forge_path, olympix_path, temp, test_skeleton_path):
        self.forge_path = forge_path
        self.src_path = os.path.join(forge_path, "src")
        self.test_path = os.path.join(forge_path, "test")
        self.analysis_data = self.olympix_static_analysis(olympix_path, self.src_path)
        self.test_skeleton = read_file(test_skeleton_path)
        self.id = str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S_'))
        self.generated_tests = {}

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
        """
        Performs static analysis on Solidity source code using Olympix.

        Args:
            olympix_path (str): Path to the Olympix executable.
            working_dir (str): Directory containing the source files to analyze.

        Returns:
            str: JSON output from the Olympix analysis.

        Raises:
            FileNotFoundError: If the Olympix executable is not found.
            RuntimeError: If the Olympix analysis command fails.
            Exception: For any unexpected errors during analysis.
        """
        full_olympix_path = os.path.join(olympix_path, "olympix.exe")

        cmd = [
            full_olympix_path,
            "analyze",
            "-w",
            ".",
            "--output-format",
            "json"
        ]

        logging.info(f"Running olympix analysis command: {' '.join(cmd)}")

        try:
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

            logging.info("Olympix analysis completed successfully.")
            logging.debug(f"Olympix analysis output:\n{result.stdout}")

            return result.stdout

        except FileNotFoundError as e:
            error_msg = (
                f"Could not locate olympix.exe at '{full_olympix_path}'. "
                "Ensure the path is correct and accessible."
            )
            logging.error(error_msg)
            raise FileNotFoundError(error_msg) from e
        except Exception as e:
            logging.error(f"Unexpected error while running olympix.exe: {e}")
            raise

    def generate_test_for_file(self,
                               filename: str,
                               error_data: str = None,
                               test_analysis_data: dict = None) -> dict:
        """
        Generates a test contract for a specified Solidity file.

        Args:
            filename (str): The name of the Solidity file to generate a test for.
            error_data (str, optional): Additional error data to include in the test generation. Defaults to None.

        Returns:
            dict: A dictionary containing the test filename and its generated test code.

        Raises:
            FileNotFoundError: If the specified Solidity file does not exist.
            Exception: If parsing the AI model's output fails.
        """
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

        # Construct the test file path
        test_filename = f"{os.path.splitext(filename)[0]}Test.sol"
        test_file_path = os.path.join(self.test_path, test_filename)

        # Determine the prompt
        if self.test_skeleton is not None:
            template = skeleton_regeneration if error_data else skeleton_generation
            format_args = {
                'source_code': source_code,
                'analysis_data': self.analysis_data,
                'filename': os.path.splitext(filename)[0],
                'test_skeleton': self.test_skeleton
            }
        else:
            template = regeneration if error_data else generation
            format_args = {
                'source_code': source_code,
                'analysis_data': self.analysis_data,
                'filename': os.path.splitext(filename)[0]
            }

        # Add 'error_data' to format arguments if it exists
        if error_data is not None:
            format_args['error_data'] = error_data
            format_args['test_analysis'] = test_analysis_data

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
            logging.error(f"BuilderAgent: Could not parse test code from model output. Error: {e}")
            raise

        # Write the new test contract
        write_file(test_code, test_file_path)
        logging.info(f"Created/modified test file: {test_file_path}")

        # Update our in-memory dictionary
        self.generated_tests[test_filename] = test_code
        
        # Return a dictionary with this file’s new test code
        return {test_filename: test_code}


    def generate_test(self,
                      target_file: str,
                      error_data: str = None,
                      test_analysis_data: dict = None) -> dict:
        """
        Public method to generate a test for a specified Solidity file.

        Args:
            target_file (str): The name of the Solidity file to generate a test for.
            error_data (str, optional): Additional error data to include in the test generation. Defaults to None.

        Returns:
            dict: A dictionary containing the test filename and its generated test code.
        """
        if error_data is None:
            logging.info(f"Generating test for file: {target_file}")
        else:
            logging.info(f"Regenerating test for file: {target_file}")
        return self.generate_test_for_file(target_file, error_data, test_analysis_data)

    def get_analysis_data(self) -> str:
        return self.analysis_data

    def get_test_code(self, filename: str) -> str:
        """
        Retrieves the generated test code for a specified Solidity file.

        Args:
            filename (str): The name of the Solidity file whose test code is to be retrieved.

        Returns:
            str: The generated test contract code.

        Raises:
            FileNotFoundError: If the test file is not found in memory or on disk.
            IOError: If reading the test file from disk fails.
        """
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
