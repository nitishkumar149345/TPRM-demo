from constants import keys
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from vector_store.milvus_vdb.milvus_client import MilvusVectorFactory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from prompts.prompt_hub import metric_summarization_prompt, formatting_prompt
from langchain_core.output_parsers import JsonOutputParser
from schema.models import Metric



llm_model = ChatOpenAI(openai_api_key=keys.OPENAI_API_KEY)
embedding_model = OpenAIEmbeddings(openai_api_key=keys.OPENAI_API_KEY)
output_parser = JsonOutputParser(pydantic_object= Metric)


def summarizer(collection_id: str, document_id: str):

    vdb = MilvusVectorFactory().init_vdb(collection_name= collection_id)

    @tool("retriever")
    def retriever(query:str):
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

        results = vector_search_results + full_text_results
        return results



    prompt = ChatPromptTemplate.from_messages([
        ('system',metric_summarization_prompt),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
        ("user", "{input}"),
    ])


    tools = [retriever]
    summarization_agent = create_tool_calling_agent(llm_model, tools, prompt)
    return AgentExecutor(agent= summarization_agent, tools= tools, verbose= True)



def formatter():

    formatter_prompt = ChatPromptTemplate.from_messages([
        ('system', formatting_prompt),
        ('user','{input}')
    ])

    return formatter_prompt | llm_model | output_parser
