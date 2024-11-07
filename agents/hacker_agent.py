import logging
import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from prompts.hacker.hacker_first_attempt import hacker_first_attempt
from prompts.hacker.hacker_incorrect_format import hacker_incorrect_format_prompt
from prompts.hacker.hacker_reattempt import hacker_reattempt
from models.HackerModelOutput import HackerModelOutput

class HackerAgent:
    def __init__(self, victim_sol_content, exploit_contract_skeleton, test_case_skeleton):
        self.ai_model = ChatOpenAI(
            model="o1-mini",
            temperature=1,
            # max_completion_tokens=3000,
            openai_api_key=os.environ["OPENAI_API_KEY"]
        )
        self.victim_sol_content = victim_sol_content
        self.exploit_contract_skeleton = exploit_contract_skeleton
        self.test_case_skeleton = test_case_skeleton
        
        self.workflow = StateGraph(state_schema=MessagesState)
        
        def call_model(state: MessagesState):
            response = self.ai_model.invoke(state["messages"])
            return {"messages": response}
        
        self.workflow.add_edge(START, "model")
        self.workflow.add_node("model", call_model)

        memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=memory)

        # Initialize logger for HackerAgent
        self.logger = logging.getLogger(__name__)
        handler = logging.FileHandler("logs/hacker_agent.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def attempt(self, forge_output=None):
        if (forge_output == None):
            prompt = hacker_first_attempt.format(victim_sol_content=self.victim_sol_content, 
                                             exploit_contract_skeleton=self.exploit_contract_skeleton, 
                                             test_case_contract=self.test_case_skeleton)
        else:
            prompt = hacker_reattempt.format(forge_test_output=forge_output)

        # print(f"This is the prompt: {prompt}")

        self.current_prompt = prompt
            
        input_messages = [HumanMessage(prompt)]
        config = {"configurable": {"thread_id": "hacker"}}

        output = self.app.invoke({"messages": input_messages}, config)
        return self.format_output(output), prompt

    def format_output(self, model_output, attempts = 3):  
        curr_attempt = 0  
        result = self.parse_output(model_output)
        while (result == None and curr_attempt < attempts):
            result = self.retry_incorrect_format()
            curr_attempt += 1
            if curr_attempt == attempts:
                logging.error("In 'hacker_agent: format_output()': Failed to generate output in correct format.")
                raise Exception("In 'hacker_agent: format_output()': Failed to generate output in correct format.")
        # print(f"This is the response: {result.explanation}")
        return result
    
    def retry_incorrect_format(self):
        input_messages = [HumanMessage(hacker_incorrect_format_prompt)]
        config = {"configurable": {"thread_id": "hacker"}}

        # print(f"This is the retry incorrect prompt: {hacker_incorrect_format_prompt}")
        
        output = self.app.invoke({"messages": input_messages}, config)
        return self.parse_output(output)

    def parse_output(self, model_output):
        try:
            # human_prompt = dict(model_output)['messages'][0].content
            ai_response = dict(model_output)['messages'][1].content
            output_dict = json.loads(ai_response)
            return HackerModelOutput(
                solidity_attempt=output_dict['my_attempt'],
                explanation=output_dict['my_explanation']
            )
        except json.JSONDecodeError:
            logging.error(f"Failed to decode JSON from: {ai_response}")
            return None
        except KeyError as e:
            logging.error(f"Expected key not found in output: {e}")
            return None

    def write_exploit(self, solidity_attempt, filepath):
        with open(filepath, "w") as f:
            f.write(solidity_attempt)
