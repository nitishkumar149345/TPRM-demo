from typing import TypedDict, Union, Dict
from langgraph.graph import StateGraph
# from langgraph.graph import add_messages

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import  ChatOpenAI

from constants import keys
from schema.models import MetricComparisonResult


llm_model = ChatOpenAI(openai_api_key= keys.OPENAI_API_KEY)

class AgentState(TypedDict):

    actual_metric: Union[Dict, str]
    target_metric: Union[Dict, str]
    condition: str

    result: str
    is_valied: dict
    result_obj: dict



def compare(state: AgentState):

    base_prompt = '''

        You are an analytical expert.

        Your task is to compare the actual metric value with the target metric value using the provided condition, and determine if the condition is satisfied.

        Follow these steps to perform the comparison:

            1. Analyze the actual and target values, including their units and the condition type (e.g., greater than, equal to, within range).
            2. Based on the relationship between the actual and target:
            - Assign **Remark** indicating trend of performace compared to target:
                - "constant" if actual equals target.
                - "up" if actual exceeds target (consider the condition to determine if this is favorable).
                - "down" if actual is below target (again, evaluate based on the condition).
            3. If the condition is not satisfied, explain **why** it failed.

        Guidelines for the response:

            1. Clearly state whether the condition is met (`True` or `False`).
            2. Provide the **Remark** describing the trend ("constant", "up", or "down").
            3. If the condition is not met, include a **Reason** explaining the failure. Be specific and include both actual and target values for clarity.
        
        Warning:
        For example, if the actual value is 3.5, the target value is 5, and the condition is <=, the evaluation should be: 3.5 <= 5, which results in true.
        Only return a boolean value (true or false) as the result of the comparison. Do not perform a textual or logical reinterpretation of the condition. Just evaluate it directly.

        '''
    
    prompt = ChatPromptTemplate.from_messages([
        ('system', base_prompt),
        ('user','{input}')
    ])

    chain = prompt | llm_model 

    actual_metric = state['actual_metric']
    target_metric = state['target_metric']
    condition = state['condition']

    input_query = f"Analyze the actual metric value: {actual_metric} against the target metric value: {target_metric}, and determine whether the condition '{condition}' is satisfied or not."

    print ('analyzing metrics........')
    result = chain.invoke({"input": input_query})
    # print (result)
    return {"result": result.content}


def formatter(state: AgentState):

    result = state['result']

    base_prompt = '''

        You are an excellent writing formatter, skilled in converting plain text into insightful and structured JSON objects.

        Your task is to understand the provided plain text data, which contains comparison details of a contract metric, and format it into a valid JSON object following the specified structure.

        The JSON should contain the following fields:

        - `is_compliant`: (bool) Indicates whether the condition between actual and target metric is met.
        - `remark`: (string) One of `"constant"`, `"up"`, or `"down"` — representing the trend of performance compared to the target.
        - `reason`: (string) A brief explanation mentioning the actual and target values, and why the condition passed or failed.

        Return only the valid JSON object as output.
        Follow these format instructions:
        {format_instructions}
        '''
    

    prompt = ChatPromptTemplate.from_messages([
        ('system', base_prompt),
        ('user','{input}')
    ])

    output_parser = JsonOutputParser(pydantic_object= MetricComparisonResult)
    chain = prompt | llm_model | output_parser

    input_query = f'format this comparsion data:{result}, \n\n from text into valied json data'
    response = chain.invoke({"input":input_query, "format_instructions": output_parser.get_format_instructions()})
    return {"result_obj": response}



workflow = StateGraph(AgentState)


workflow.add_node('analyzer', compare)
workflow.add_node('formatter', formatter)

workflow.add_edge('analyzer','formatter')

workflow.set_entry_point('analyzer')
workflow.set_finish_point('formatter')

agent = workflow.compile()



if __name__ == '__main__':
    inputs = {
        "actual_metric": "85 %",
        "target_metric": "83 %",
        "condition": ">= greater than or equals to",
    }


    result = agent.invoke(inputs)
    print (result)

