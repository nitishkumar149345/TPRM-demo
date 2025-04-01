import os

from constants import keys
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

# from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from vector_store.milvus_vdb.milvus_client import MilvusVectorFactory
from vector_store.models import Document


class PreprocessDocument:
    def __init__(self, document_path: str, collection_name: str, document_id: str):
        self._vdb_client = MilvusVectorFactory().init_vdb(
            collection_name=collection_name
        )
        self.document_path = document_path
        self.document_id = document_id
        self.openai_embedding_model = OpenAIEmbeddings(openai_api_key = keys.OPENAI_API_KEY)
        # self.embedding_model = HuggingFaceEmbeddings(
        #     model_name="sentence-transformers/all-mpnet-base-v2"
        # )

        if not os.path.exists(document_path):
            raise FileNotFoundError

    def process_document(
        self,
    ):
        loader = PyMuPDFLoader(self.document_path)
        docs = loader.load()

        splitter = SemanticChunker(embeddings=self.openai_embedding_model)
        chunks = splitter.split_documents(docs)

        texts = [chunk.page_content for chunk in chunks]
        print ('embedding started......................')
        embeddings = self.openai_embedding_model.embed_documents(texts= texts)
        print ('finished embedding chunks..............')
        document_id = self.document_id

        text_objs = [
            Document(
                page_content=chunk.page_content,
                vector=embedding,
                metadata= {**chunk.metadata, 'document_id':document_id},
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]

        self._vdb_client.create(texts=text_objs, embeddings=embeddings)
    