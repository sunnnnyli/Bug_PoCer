import logging
import os
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from typing_extensions import Annotated, TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from lib.forge_lib import ForgeLib
from agents.tester.prompts.analyze_test import analyze_test
from agents.tester.prompts.chained_call import chained_call
from lib.file_lib import write_file, read_file


class TestOutput(TypedDict):
    status: Annotated[
        str,
        ...,
        "The result status: 'success', 'builder_error', 'hacker_failure', or 'unknown'."
    ]
    feedback: Annotated[
        str,
        ...,
        "Detailed feedback explaining the reason for the test result."
    ]
    suggestions: Annotated[
        str,
        ...,
        "Actionable suggestions for the relevant agent to address the issue."
    ]


class TesterAgent:
    def __init__(self, gpt_model: str, forge_path: str, temp: int):
        self.forge_path = forge_path
        self.src_path = os.path.join(forge_path, "src")
        self.test_path = os.path.join(forge_path, "test")
        self.exploit_path = os.path.join(forge_path, "exploits")
        self.test_output = None
        self.id = str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S_'))

        self.ai_model = ChatOpenAI(
            model=gpt_model,
            temperature=temp,
            openai_api_key=os.environ["OPENAI_API_KEY"]
        )

        self.chained_model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=os.environ["OPENAI_API_KEY"]
        ).with_structured_output(TestOutput)

        # Build a workflow graph for the AI calls
        self.workflow = StateGraph(state_schema=MessagesState)

        def call_model(state: MessagesState):
            response = self.ai_model.invoke(state["messages"])
            return {"messages": response}

        self.workflow.add_edge(START, "model")
        self.workflow.add_node("model", call_model)

        memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=memory)


    def run_test(self, filename: str) -> TestOutput | None:
        test_filename = f"{os.path.splitext(filename)[0]}Test.sol"
        logging.info(f"Testing exploit code for {test_filename}...")

        try:
            forge_output = ForgeLib.run_forge_test(self.forge_path, filename)
            self.test_output = forge_output.output_str
        except Exception as e:
            logging.error(f"Failed to run Forge test: {e}")
            return None  # Indicates an internal error with the tester

        logging.info(f"Forge Output:\n{forge_output.output_str}")

        if forge_output.return_code == 0:
            logging.info("Successfully exploited the code!")
            return TestOutput(
                status="success",
                feedback="The exploit was successfully executed.",
                suggestions="No further action required."
            )
        else:
            # Use AI to analyze the failure reason

            logging.info("Analyzing the forge output...")
            test_result = self._analyze_forge_output(filename, forge_output.output_str)
            logging.info(f"Analysis output: {test_result}")
            return test_result


    def _analyze_forge_output(self, filename: str, output_str: str) -> TestOutput:
        exploit_filename = f"{os.path.splitext(filename)[0]}Exploit.sol"
        test_filename = f"{os.path.splitext(filename)[0]}Test.sol"

        source_file_path = os.path.join(self.src_path, filename)
        exploit_file_path = os.path.join(self.exploit_path, exploit_filename)
        test_file_path = os.path.join(self.test_path, test_filename)
        
        prompt = analyze_test.format(
            source_filename=filename,
            source_contract=read_file(source_file_path),
            exploit_filename=exploit_filename,
            exploit_contract=read_file(exploit_file_path),
            test_filename=test_filename,
            test_contract=read_file(test_file_path),
            forge_output=output_str
        )
        logging.info(f"Prompt fed to tester agent:\n{prompt}")

        input_messages = [HumanMessage(prompt)]
        config = {"configurable": {"thread_id": self.id}}

        logging.info("Invoking tester agent...")
        output = self.app.invoke({"messages": input_messages}, config)
        logging.info("Tester agent returned a response.")

        try:
            o1_json_response = output["messages"][-1].content
            chained_prompt = chained_call.format(ai_response=o1_json_response)

            logging.info(f"Prompt fed to tester agent's chained model:\n{chained_prompt}")

            output_dict = self.chained_model.invoke(chained_prompt)
            logging.info("Tester agent's chained model returned a response.")

            # status = output_dict['status']
            # feedback = output_dict['feedback']
            # suggestions = output_dict['suggestions']

            return output_dict  # This will be a TestOutput TypedDict
        except Exception as e:
            logging.error(f"AI Analysis failed: {e}")
            return TestOutput(
                status="unknown",
                feedback="AI failed to analyze the Forge output.",
                suggestions="Manual inspection is required."
            )
        

    def get_forge_output(self) -> str:
        return self.test_output
    

    def reset_forge_output(self):
        self.test_output = None
