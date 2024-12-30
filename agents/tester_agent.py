import logging
import os
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from typing_extensions import Annotated, TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from forge_lib import ForgeLib
from prompts.tester.analyze_test import analyze_test
from prompts.tester.chained_call import chained_call


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
        """
        Executes the generated test contract using Forge and returns a structured TestOutput.

        Args:
            filename (str): The name of the Solidity file whose test is to be run.
        """
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
            test_result = self._analyze_forge_output(forge_output.output_str)
            logging.info(f"Analysis output: {test_result}")
            return test_result

    def _analyze_forge_output(self, output_str: str) -> TestOutput:
        """
        Uses the AI model to analyze Forge output and determine the reason for test failure.

        Args:
            output_str (str): The output string from Forge.

        Returns:
            TestOutput: A structured result indicating the failure reason and suggestions.
        """
        prompt = analyze_test.format(forge_output=output_str)
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
    