import os

from constants import keys
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

# from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from vector_store.milvus_vdb.milvus_client import MilvusVectorFactory
from vector_store.models import Document
from logger_config.logs import logger


class PreprocessDocument:
    def __init__(self, document_path: str, collection_name: str, document_id: str):
        logger.info(f"Initializing document processor for: {document_path}")
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
            logger.error(f"Document not found: {document_path}")
            raise FileNotFoundError

    def process_document(
        self,
    ):
        loader = PyMuPDFLoader(self.document_path)
        docs = loader.load()

        logger.info("Splitting document into chunks")
        splitter = SemanticChunker(embeddings=self.openai_embedding_model)
        chunks = splitter.split_documents(docs)
        logger.info(f"Created {len(chunks)} semantic chunks")

        texts = [chunk.page_content for chunk in chunks]
        
        logger.info("Generating embeddings")
        embeddings = self.openai_embedding_model.embed_documents(texts=texts)
        logger.info("Embeddings generated")

        text_objs = [
            Document(
                page_content=chunk.page_content,
                vector=embedding,
                metadata={**chunk.metadata, 'document_id': self.document_id},
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]

        logger.info("Storing in vector database")
        self._vdb_client.create(texts=text_objs, embeddings=embeddings)
        logger.info("Document processing completed")
            
    # except Exception as e:
    #     logger.error(f"Error in document processing: {str(e)}")
    #     raise
    