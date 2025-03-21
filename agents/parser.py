import json
import os
import pathlib
from typing import List

from constants import keys
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from logger_config.logs import logger

parent_path = pathlib.Path(__file__).parent.parent
fields_path = os.path.join(parent_path, "schema", "msa_schema.json")
# print (fields_path)

if not os.path.exists(fields_path):
    raise FileExistsError


class Extractor:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.metadata = {}
        self.llm_model = ChatOpenAI(openai_api_key=keys.OPENAI_API_KEY, temperature=0)
        # self.retriever = None

        if not os.path.exists(self.file_path):
            raise FileNotFoundError

    @staticmethod
    def load_questionnair(fields: list) -> List[str]:
        questionnair = [
            f"What is {field} and what is the {field} metric value" for field in fields
        ]

        return questionnair

    def process_file(
        self,
    ) -> SelfQueryRetriever:
        loader = PyMuPDFLoader(self.file_path)
        docs = loader.load()

        logger.info("sematic chunking initiated")
        splitter = SemanticChunker(embeddings=OpenAIEmbeddings())
        chunks = splitter.split_documents(docs)
        # print ('chunking completed')

        vector_database = Chroma.from_documents(chunks, OpenAIEmbeddings())

        retriever = SelfQueryRetriever.from_llm(
            llm=self.llm_model,
            vectorstore=vector_database,
            document_contents="",
            metadata_field_info=[],
        )

        return retriever

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
        retriever = self.process_file()
        metrics = self.get_fields()

        questions = Extractor.load_questionnair(fields=metrics)

        for question, field in zip(questions, metrics):
            logger.info(f"collecting data: {field}")
            chunks = retriever.invoke(question)

            self.metadata[field] = chunks

        return self.metadata


# c = Extractor(file_path=r'C:\Users\Nitish Kumar\Desktop\TPRM_Agents\contracts\CareConnect Solutions Master Services Agreement.pdf')
# from rich import print
# print (c.collect_data())
