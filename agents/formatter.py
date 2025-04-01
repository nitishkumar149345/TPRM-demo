import json
import os
import pathlib
from typing import Any, Dict, List

from constants import keys
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from logger_config.logs import logger
from schema.models import Metric
from vector_store.milvus_vdb.milvus_client import MilvusVectorFactory

parent_path = pathlib.Path(__file__).parent.parent
fields_path = os.path.join(parent_path, "schema", "msa_schema.json")


if not os.path.exists(fields_path):
    raise FileExistsError


class MetricExtractor:
    def __init__(self, document_id: str, collection_id: str):
        self.document_id = document_id
        self.collection_id = collection_id
        self._llm_model = ChatOpenAI(openai_api_key=keys.OPENAI_API_KEY)
        self._output_parser = JsonOutputParser(pydantic_object=Metric)

    @staticmethod
    def load_questionnair(fields: list) -> List[str]:
        questionnair = [
            f"""What are all the details, definitions, evaluation criteria, thresholds, penalties, bonuses, and 
            related clauses associated with {field} in this contract?"""
            for field in fields
        ]

        return questionnair

    def get_fields(
        self,
    ):
        with open(fields_path, "r") as f:
            fields = json.load(f)
            fields = list(fields.keys())

        return fields

    def collect_data(
        self,
    ):
        metrics = self.get_fields()
        questionnaire = MetricExtractor.load_questionnair(fields=metrics)

        vdb = MilvusVectorFactory().init_vdb(collection_name=self.collection_id)

        metadata = {}
        for query, metric in zip(questionnaire, metrics):
            print(f"collecting data:{metric}")
            query_vector = OpenAIEmbeddings().embed_query(text=query)

            vector_search_results = vdb.search_by_vector(
                query_vector=query_vector, document_ids=[self.document_id]
            )
            full_text_search_results = vdb.search_by_full_text(
                query=query, document_ids=[self.document_id]
            )

            metadata[metric] = vector_search_results[0] + full_text_search_results[0]

        return metadata

    def _setup_chain(
        self,
    ):
        """Set up the processing chain with prompt template and parser."""
        base_prompt = """

        Role: Act as an Senior Compliance Officer, experienced in analyzing service level aggrement contracts and formulating various sla metrics.

        Task: Your task is to understand, analyze and identify various SLA Performance metrics from the given SLA contract document.
        
        Guidelines: To perform the specified task, follow these steps:
            - Read and understand the sla metrics from the contract document.
            - Identify and classify performance metrics like uptime, response time, resolutuion_time, throughput, latency, capacity, error rate, mean_time_between_failures, and mean_time_to_repair from mentiones sla metrics in contract.
        
        Input: You will receive the contract as complete text: {context}
        
        Output: Respond with identified SLA Performance Metrics in specified format.
        
        \n\n
        format_instructions: {format_instructions}
        """

        prompt = ChatPromptTemplate.from_messages(
            [("system", base_prompt), ("user", "{input}")]
        )
        return prompt | self._llm_model | self._output_parser

    def process_metrics(self) -> Dict[str, Any]:
        """Process all metrics from the document and return results."""
        logger.info("strating metrics processing")

        try:
            metadata = self.collect_data()
            metrics = list(metadata.keys())

            final_metrics = {}

            for metric in metrics:
                print(f"processing metric:{metric}")

                data = metadata.get(metric)
                context = "".join(chunk["entity"]["page_content"] for chunk in data)
                query = f"collect all data related to the metric {metric} and format in specified json"

                chain = self._setup_chain()

                response = chain.invoke(
                    {
                        "context": context,
                        "format_instructions": self._output_parser.get_format_instructions(),
                        "input": query,
                    }
                )

                final_metrics[metric] = {
                    "result": response,
                    # "source": metadata[metric]
                }

            return final_metrics

        except Exception as e:
            print(e)
            raise Exception


# m = MetricExtractor(document_id='01', collection_id='_01')
# print (m.process_metrics())
