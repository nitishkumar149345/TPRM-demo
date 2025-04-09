from constants import keys

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_core.runnables.base import RunnableSequence

from vector_store.milvus_vdb.milvus_client import MilvusVectorFactory
from typing import Any, Dict, Optional, TypedDict, Union
from langgraph.graph import StateGraph

from schema.models import Metric



llm_model = ChatOpenAI(openai_api_key= keys.OPENAI_API_KEY)
embedding_model = OpenAIEmbeddings(openai_api_key= keys.OPENAI_API_KEY)


class AgentState(TypedDict):

    field_name: str
    collection_id: str
    document_id: str
    summary: str
    result_obj: dict


metric_schema = '''
"matric_value": {{"min_value":"<value>", "max_value":"<value>", "data_type":"<datatype>"}},
"condition": "<condition>",
"frequency":"<frequency>",
"description":"<description>"
'''


def summarizer(state: AgentState):

    collection_id = state['collection_id']
    document_id = state['document_id']

    field = state['field_name']

    vdb = MilvusVectorFactory().init_vdb(collection_name= collection_id)
    
    @tool("custom_retriever")
    def custom_retriever(query: str)->list:
        """Retrieval tool to get related chunk content of query"""
        

        query_vector = OpenAIEmbeddings(openai_api_key= keys.OPENAI_API_KEY).embed_query(text= query)

        vector_search_results = vdb.search_by_vector(query_vector= query_vector, document_ids= [document_id])
        full_text_results = vdb.search_by_full_text(query= query, document_ids= [document_id])
        # print (vector_search_results)

        results = vector_search_results + full_text_results
        return results
    
    
    prompt = ChatPromptTemplate.from_messages([
    ('system','''
        You are a contract metric summarizer.
        Your task is to generate a structured summary related to a specific metric or performance field found within a given contract.

        Inputs:

        Metric or Performance Field: {field_name}

        Tools:
        You have access to a tool called custom_retriever, which retrieves the most relevant contract content based on a query.

        Follow this step-by-step reasoning:

        Formulate a focused query based on the input {field_name} to retrieve all content that could mention the relevant metric and its associated thresholds, conditions, frequency, or description.

        Example query format: "Information related to [field_name] metric, including threshold values, evaluation frequency, and description."

        Use custom_retriever with this query to extract the most relevant chunks from the contract.

        Analyze the retrieved content carefully to extract the following details:

        Minimum Value — Set if value is like ≥ X, or if a range is provided, should contain only numerical value, int, float, etc.

        Maximum Value — Set if value is like ≤ Y, or if a range is provided. should contain only numerical value, int, float, etc

        Condition — The condition or scenario under which the metric is applicable or monitored, (>= grater than equals to, <= less than equal to, = equal to, etc..)
                    You might get the condition near value. 
        
        Frequency — How frequently the metric is evaluated, (daily, weekly, monthly, quaterly, yearly, etc.)

        Description — A one-line explanation of what the metric measures.

        If any of these fields are not found, explicitly mark them as "not found" in the output.
            '''),
        MessagesPlaceholder(variable_name='agent_scratchpad'),
        ('user','{input}')
    ])

    tools = [custom_retriever]
    agent = create_tool_calling_agent(llm_model, tools, prompt)
    agent_executor = AgentExecutor(agent= agent, tools= tools, verbose= True)

    result = agent_executor.invoke({"field_name":field, "input":"extract all details related to field and give summary with specified details"})
    return {"summary": result['output']}



def formatter(state: AgentState):

    summary = state['summary']

    base_prompt = '''

    You are a data extraction engine. Your task is to extract structured information from the following input text and map it into the provided JSON schema.

        Input:
        Input text content: {context}
        Map the text with this json schema: {schema}

        Instructions:

        Carefully read and understand the input text.

        Match the content with the fields in the JSON schema.

        If a specific field is not present in the input text or the value is unclear, set that field’s value as null.

        Ensure the output is a valid JSON object with all fields from the schema.

    Follow these format instructions for output model:
    {format_instructions}
    '''
    prompt = ChatPromptTemplate.from_messages([
        ('system', base_prompt),
        ('user','{input}')
    ])

    parser = JsonOutputParser(pydantic_object=Metric)
    chain = prompt | llm_model | parser

    data = chain.invoke({
        "context": summary,
        "schema": metric_schema,
        "format_instructions":parser.get_format_instructions(),
        "input": "understand the given context data, and format it as json"
        })
    return {"result_obj": data}


workflow = StateGraph(AgentState)

workflow.add_node('summarizer', summarizer)
workflow.add_node('formatter', formatter)

workflow.add_edge('summarizer','formatter')

workflow.set_entry_point('summarizer')
workflow.set_finish_point('formatter')

agent =workflow.compile()


result = agent.invoke({"collection_id":"_caa67daa_ab19_454e_8e9d_7f9b0d194dec", 
                       "document_id":"5f966009-e6b5-42be-b6f2-058d0d46c859",
                       "field_name":"average handel time"})

print (result['result_obj'])

