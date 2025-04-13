from typing import TypedDict

from constants import keys
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import StateGraph
from schema.models import MetadataValue, Metric
from vector_store.milvus_vdb.milvus_client import MilvusVectorFactory

from prompts.prompt_hub import base_field_instructions, metric_field_instructions, base_schema, metric_schema

llm_model = ChatOpenAI(openai_api_key=keys.OPENAI_API_KEY)
embedding_model = OpenAIEmbeddings(openai_api_key=keys.OPENAI_API_KEY)


class AgentState(TypedDict):
    field_name: str
    collection_id: str
    document_id: str
    field_type: str
    summary: str
    result_obj: dict


# base_field_instructions = """
# Formulate a focused query based on the input {field_name} to retrieve all content that could mention the relevant answer for field.

# Example query format: "what is name of the contract - contract_name"
# Use custom_retriever with this query to extract the most relevant chunks from the contract.
# 1.  Carefully analyze the context to find the exact, straightforward answer for the field "{field_name}".


# ** The answer may not be startght forwaord or explicitly mentioned, but you can think similar data for filed as answer.
# """


def summarizer(state: AgentState):
    collection_id = state["collection_id"]
    document_id = state["document_id"]

    field = state["field_name"]
    # print(field)

    vdb = MilvusVectorFactory().init_vdb(collection_name=collection_id)

    @tool("custom_retriever")
    def custom_retriever(query: str) -> list:
        """Retrieval tool to get related chunk content of query"""

        query_vector = OpenAIEmbeddings(openai_api_key=keys.OPENAI_API_KEY).embed_query(
            text=query
        )

        vector_search_results = vdb.search_by_vector(
            query_vector=query_vector, document_ids=[document_id]
        )
        full_text_results = vdb.search_by_full_text(
            query=query, document_ids=[document_id]
        )
        # print (vector_search_results)

        results = vector_search_results + full_text_results
        return results

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
        You are a contract metric summarizer.
        Your task is to generate a structured summary related to a specific metric or performance field found within a given contract.

        Inputs:

        Metric or Performance Field: {field_name}

        Tools:
        You have access to a tool called custom_retriever, which retrieves the most relevant contract content based on a query.

        Follow this step-by-step reasoning:

        {schema_instructions}

        If any of these fields are not found, explicitly mark them as "not found" in the output.
            """,
            ),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
            ("user", "{input}"),
        ]
    )

    tools = [custom_retriever]
    agent = create_tool_calling_agent(llm_model, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

    if state["field_type"] == "base":
        result = agent_executor.invoke(
            {
                "field_name": field,
                "schema_instructions": base_field_instructions,
                "input": "Understand the context and identify correct answer for field.",
            }
        )
    else:
        result = agent_executor.invoke(
            {
                "field_name": field,
                "schema_instructions": metric_field_instructions,
                "input": "extract all details related to field and give summary with specified details",
            }
        )

    return {"summary": result["output"]}


def formatter(state: AgentState):
    summary = state["summary"]

    base_prompt = """

    You are a data extraction engine. Your task is to extract structured information from the following input text and map it into the provided JSON schema.

        Input:
        Input text content: {context}
        Map the text with this json schema: {schema}

        Instructions:

        Carefully read and understand the input text.

        Match the content with the fields in the JSON schema.
        You should use only the fields specified in schema. Do use any other keys. Stick to the given schema.
        
        If data for specific field is not present in the input text or the value is unclear, set that field’s value as null.

        Ensure the output is a valid JSON object with all fields from the schema.

    Follow these format instructions for output model:
    {format_instructions}
    """
    prompt = ChatPromptTemplate.from_messages(
        [("system", base_prompt), ("user", "{input}")]
    )

    if state["field_type"] == "base":
        parser = JsonOutputParser(pydantic_object=MetadataValue)
        schema = base_schema
    else:
        parser = JsonOutputParser(pydantic_object=Metric)
        schema = metric_schema

    chain = prompt | llm_model | parser

    data = chain.invoke(
        {
            "context": summary,
            "schema": schema,
            "format_instructions": parser.get_format_instructions(),
            "input": "understand the given context data, and format it as json",
        }
    )

    return {"result_obj": data}


workflow = StateGraph(AgentState)

workflow.add_node("summarizer", summarizer)
workflow.add_node("formatter", formatter)

workflow.add_edge("summarizer", "formatter")

workflow.set_entry_point("summarizer")
workflow.set_finish_point("formatter")

agent = workflow.compile()


if __name__ == "__main__":
    result = agent.invoke(
        {
            "collection_id": "_caa67daa_ab19_454e_8e9d_7f9b0d194dec",
            "document_id": "5f966009-e6b5-42be-b6f2-058d0d46c859",
            "field_name": "what type (msa, sla, nda, etc) of contract is this?",
            "field_type": "base",
        }
    )

    print(result["result_obj"])
