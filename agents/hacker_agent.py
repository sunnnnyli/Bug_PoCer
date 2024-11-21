import logging
import os
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from typing_extensions import Annotated, TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from prompts.hacker.hacker_first_attempt import hacker_first_attempt
from prompts.hacker.hacker_incorrect_format import hacker_incorrect_format_prompt
from prompts.hacker.hacker_reattempt import hacker_reattempt
from prompts.hacker.hacker_chained_call import hacker_chained_call
from models.HackerModelOutput import HackerModelOutput


class StructuredOutput(TypedDict):
    my_attempt: Annotated[str, ..., "Your full exploit code"]
    my_explanation: Annotated[str, ..., "Explanation of your attempt"]


class HackerAgent:
    def __init__(self, ethernaut_challenge, victim_sol_content, exploit_contract_skeleton, test_case_skeleton):
        self.ai_model = ChatOpenAI(
            model="o1-preview",
            temperature=1, # O1 only supports temp 1 for now
            openai_api_key=os.environ["OPENAI_API_KEY"]
        )

        self.chained_model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=os.environ["OPENAI_API_KEY"]
        ).with_structured_output(StructuredOutput)
        
        self.ethernaut_challenge = ethernaut_challenge
        self.victim_sol_content = victim_sol_content
        self.exploit_contract_skeleton = exploit_contract_skeleton
        self.test_case_skeleton = test_case_skeleton
        self.id = str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S_')) + str(self.ethernaut_challenge)
        
        self.workflow = StateGraph(state_schema=MessagesState)
        
        def call_model(state: MessagesState):
            response = self.ai_model.invoke(state["messages"])
            return {"messages": response}
        
        self.workflow.add_edge(START, "model")
        self.workflow.add_node("model", call_model)

        memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=memory)

    
    def attempt(self, forge_output=None):
        if (forge_output == None):
            prompt = hacker_first_attempt.format(victim_sol_content=self.victim_sol_content, 
                                                 exploit_contract_skeleton=self.exploit_contract_skeleton, 
                                                 test_case_contract=self.test_case_skeleton)
        else:
            prompt = hacker_reattempt.format(forge_test_output=forge_output)

        logging.info(f"Prompt fed to the main AI model:\n{prompt}")

        input_messages = [HumanMessage(prompt)]
        config = {"configurable": {"thread_id": self.id}}

        output = self.app.invoke({"messages": input_messages}, config)
        logging.info(f"Main AI model returned a response")
        return self.format_output(output)
    

    def format_output(self, model_output, attempts = 3):  
        curr_attempt = 0
        result = self.parse_output(model_output)
        while (result == None and curr_attempt < attempts):
            result = self.retry_incorrect_format()
            curr_attempt += 1
            if curr_attempt == attempts:
                logging.error("AI failed to generate output in correct format")
                raise Exception("'hacker_agent: format_output()': Failed to generate output in correct format.")
        return result
    

    def retry_incorrect_format(self):
        input_messages = [HumanMessage(hacker_incorrect_format_prompt)]
        config = {"configurable": {"thread_id": self.id}}
        
        output = self.app.invoke({"messages": input_messages}, config)
        return self.parse_output(output)


    def parse_output(self, model_output):
        try:
            o1_json_response = model_output['messages'][-1].content  # JSON in string format
            prompt = hacker_chained_call.format(ai_response=o1_json_response)

            logging.info(f"Prompt fed to the chained call AI model:\n{prompt}")

            output_dict = self.chained_model.invoke(prompt)
            logging.info(f"Chained AI model returned a response")
            parsed_output = HackerModelOutput(
                solidity_attempt=output_dict['my_attempt'],
                explanation=output_dict['my_explanation']
            )
            return parsed_output
        except KeyError:
            logging.error(f"Expected key 'my_attempt' or 'my_explanation' not found in output: {parsed_output}")
            return None


    def write_exploit(self, solidity_attempt, filepath):
        with open(filepath, "w") as file:
            file.write(solidity_attempt)
            logging.info(f"Exploit code written to {filepath}")
