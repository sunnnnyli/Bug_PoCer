import logging
import os
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from typing_extensions import Annotated, TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from prompts.hacker.first_attempt import first_attempt
from prompts.hacker.skeleton_first_attempt import skeleton_first_attempt
from prompts.hacker.reattempt import reattempt
from prompts.hacker.skeleton_reattempt import skeleton_reattempt
from prompts.hacker.chained_call import chained_call
from lib.file_lib import write_file, read_file


class HackOutput(TypedDict):
    my_exploit: Annotated[str, ..., "Your full exploit code"]
    my_explanation: Annotated[str, ..., "Explanation of your exploit code"]


class HackerAgent:
    def __init__(self, gpt_model, forge_path, temp, exploit_skeleton_path):
        self.forge_path = forge_path
        self.src_path = os.path.join(forge_path, "src")
        self.exploit_skeleton = read_file(exploit_skeleton_path)
        self.id = str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S_'))
        self.generated_exploits = {}

        self.ai_model = ChatOpenAI(
            model=gpt_model,
            temperature=temp,
            openai_api_key=os.environ["OPENAI_API_KEY"]
        )

        self.chained_model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=os.environ["OPENAI_API_KEY"]
        ).with_structured_output(HackOutput)
        
        self.workflow = StateGraph(state_schema=MessagesState)
        
        def call_model(state: MessagesState):
            response = self.ai_model.invoke(state["messages"])
            return {"messages": response}
        
        self.workflow.add_edge(START, "model")
        self.workflow.add_node("model", call_model)

        memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=memory)

    def exploit(self,
                static_analysis,
                filename,
                test_code,
                forge_output=None,
                exploit_analysis_data: dict = None) -> dict:
        src_file_path = os.path.join(self.src_path, filename)

        # Determine the template and formatting arguments based on conditions
        if forge_output is None:
            template = first_attempt if self.exploit_skeleton is None else skeleton_first_attempt
            format_args = {
                "source_code": read_file(src_file_path),
                "analysis_data": static_analysis,
                "test_code": test_code,
                "filename": os.path.splitext(filename)[0]
            }
            if self.exploit_skeleton is not None:
                format_args["exploit_skeleton"] = self.exploit_skeleton
        else:
            template = reattempt if self.exploit_skeleton is None else skeleton_reattempt
            format_args = {
                "forge_test_output": forge_output,
                "test_analysis": exploit_analysis_data,
                "analysis_data": static_analysis
            }
            if self.exploit_skeleton is not None:
                format_args["exploit_skeleton"] = self.exploit_skeleton

        # Generate the prompt using the selected template and arguments
        prompt = template.format(**format_args)

        logging.info(f"Prompt fed to hacker agent:\n{prompt}")

        input_messages = [HumanMessage(prompt)]
        config = {"configurable": {"thread_id": self.id}}

        logging.info("Invoking hacker agent...")
        output = self.app.invoke({"messages": input_messages}, config)
        logging.info("Hacker agent returned a response.")

        # Use the second model to parse structured JSON
        try:
            o1_json_response = output["messages"][-1].content
            chained_prompt = chained_call.format(ai_response=o1_json_response)

            logging.info(f"Prompt fed to hacker agent's chained model:\n{chained_prompt}")

            output_dict = self.chained_model.invoke(chained_prompt)
            logging.info("Hacker agent's chained model returned a response.")

            exploit_code = output_dict['my_exploit']
            # explanation = output_dict['my_explanation']
        except Exception as e:
            logging.error(f"Could not parse exploit code from model output. Error: {e}")
            raise

        # Construct the exploit filename (e.g., FooExploit.sol if 'Foo.sol' was the original)
        exploit_filename = f"{os.path.splitext(filename)[0]}Exploit.sol"
        exploit_file_path = os.path.join(self.forge_path, "exploits", exploit_filename)

        # Write the exploit code to the 'exploits' folder
        write_file(exploit_code, exploit_file_path)
        logging.info(f"Created exploit file: {exploit_file_path}")

        # Store in in-memory dictionary
        self.generated_exploits[exploit_filename] = exploit_code

        # Return a dictionary with the newly created exploit file name and code
        return {exploit_filename: exploit_code}

    def get_exploit_code(self, filename: str) -> str:
        exploit_filename = f"{os.path.splitext(filename)[0]}Exploit.sol"

        # Check in-memory dictionary first
        if exploit_filename in self.generated_exploits:
            return self.generated_exploits[exploit_filename]

        # Otherwise, attempt to read from disk
        exploit_file_path = os.path.join(self.forge_path, "exploits", exploit_filename)
        if not os.path.isfile(exploit_file_path):
            error = f"Exploit file '{exploit_file_path}' not found in memory or on disk."
            logging.error(error)
            raise FileNotFoundError(error)

        try:
            code_from_disk = read_file(exploit_file_path)
            return code_from_disk
        except IOError as e:
            error = f"Failed to read exploit file '{exploit_file_path}'. Error: {e}"
            logging.error(error)
            raise e
