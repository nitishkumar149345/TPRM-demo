from typing import Optional

from packaging import version
from pymilvus import (
    CollectionSchema,
    DataType,
    FieldSchema,
    Function,
    FunctionType,
    MilvusClient,
    MilvusException,
)
from pymilvus.milvus_client import IndexParams
from pymilvus.orm.types import infer_dtype_bydata
from vector_store.base_vectorstore import BaseVector
from vector_store.fields import Field
from vector_store.models import Document, MilvusConfig
from logger_config.logs import logger
# from base_vectorstore import BaseVector
# from .fields import Field
# from .models import Document, MilvusConfig


class MilvusVector(BaseVector):
    def __init__(self, collection_name: str, config: MilvusConfig):
        super().__init__(collection_name)

        self._client = self._init_client(config=config)
        self._hybrid_search_enabled = self._check_hybrid_search_support()
        self._consistency_level = "Session"

    def _check_hybrid_search_support(self) -> bool:
        """
        Check if the current Milvus version supports hybrid search.
        Returns True if the version is >= 2.5.0, otherwise False.
        """

        try:
            milvus_version = self._client.get_server_version()
            milvus_version = milvus_version.split("/")[-1]
            return (
                version.parse(milvus_version).base_version
                >= version.parse("2.5.0").base_version
            )
        except Exception as e:
            print(str(e))
            return False

    def _init_client(self, config: MilvusConfig):
        """
        Initialize and return a Milvus client.
        """
        try:
            print (config.uri)
            client = MilvusClient(uri=config.uri)

            return client
        except MilvusException :
            raise MilvusException

      

    def create(self, texts: list[Document], embeddings: list[list[float]]):
        """
        Create a collection and add texts with embeddings.
        """
        index_params = {
            "metric_type": "IP",
            "index_type": "HNSW",
            "params": {"M": 8, "efConstruction": 64},
        }
        metadatas = [d.metadata if d.metadata is not None else {} for d in texts]
        self.create_collection(embeddings, metadatas, index_params)
        self.add_texts(texts, embeddings)

    def create_collection(
        self,
        embeddings: list[list[float]],
        metadata: Optional[list[dict]] = None,
        index_params: Optional[dict] = None,
    ):
        """
        Create a new collection in Milvus with the specified schema and index parameters.
        """

        if not self._client.has_collection(self.collection_name):
            fields = []
            dim = len(embeddings[0])

            fields.append(
                FieldSchema(
                    name=Field.PRIMARY_KEY.value,
                    dtype=DataType.INT64,
                    is_primary=True,
                    auto_id=True,
                )
            )
            fields.append(
                FieldSchema(
                    name=Field.METADATA_KEY.value,
                    dtype=DataType.JSON,
                    max_length=65_535,
                )
            )
            fields.append(
                FieldSchema(
                    name=Field.CONTENT_KEY.value,
                    dtype=DataType.VARCHAR,
                    max_length=65_535,
                    enable_analyzer=self._check_hybrid_search_support(),
                )
            )
            fields.append(
                FieldSchema(
                    name=Field.VECTOR.value,
                    dtype=infer_dtype_bydata(data=embeddings[0]),
                    dim=dim,
                )
            )

            if self._hybrid_search_enabled:
                fields.append(
                    FieldSchema(
                        name=Field.SPARSE_VECTOR.value,
                        dtype=DataType.SPARSE_FLOAT_VECTOR,
                    )
                )

                bm25_function = Function(
                    name="text_bm25_emb",
                    input_field_names=[Field.CONTENT_KEY.value],
                    output_field_names=[Field.SPARSE_VECTOR.value],
                    function_type=FunctionType.BM25,
                )

            schema = CollectionSchema(fields)
            if self._hybrid_search_enabled:
                schema.add_function(bm25_function)

            index_params_obj = IndexParams()
            index_params_obj.add_index(field_name=Field.VECTOR.value, **index_params)

            if self._hybrid_search_enabled:
                index_params_obj.add_index(
                    field_name=Field.SPARSE_VECTOR.value,
                    index_type="AUTOINDEX",
                    metric_type="BM25",
                )

            self._client.create_collection(
                collection_name=self._collection_name,
                schema=schema,
                index_params=index_params_obj,
                consistency_level=self._consistency_level,
            )

    def add_texts(self, documents: list[Document], embeddings: list[list[float]]):
        """
        Add texts and their embeddings to the collection.
        """
        insert_text_data = []
        for document, embedding in zip(documents, embeddings):
            insert_dict = {
                Field.CONTENT_KEY.value: document.page_content,
                Field.VECTOR.value: embedding,
                Field.METADATA_KEY.value: document.metadata,
            }
            insert_text_data.append(insert_dict)

        try:
            pks = self._client.insert(
                collection_name=self._collection_name, data=insert_text_data
            )
        except MilvusException as e:
            raise e

        return pks

    def search_by_vector(
        self, query_vector: list[float], document_ids: list[str]
    ) -> list[Document]:
        """
        Search for documents by vector similarity.
        """

        results = self._client.search(
            collection_name=self._collection_name,
            data=[query_vector],
            anns_field=Field.VECTOR.value,
            limit=3,
            output_fields=[Field.CONTENT_KEY.value, Field.METADATA_KEY.value],
            filter=f'metadata["document_id"] in ({document_ids})',
        )

        return results

    def search_by_full_text(
        self, query: str, document_ids: list[str]
    ) -> list[Document]:
        """
        Search for documents by full-text search (if hybrid search is enabled).
        """

        if not self._hybrid_search_enabled:
            return {}

        results = self._client.search(
            collection_name=self._collection_name,
            data=[query],
            anns_field=Field.SPARSE_VECTOR.value,
            limit=4,
            output_fields=[Field.CONTENT_KEY.value, Field.METADATA_KEY.value],
            filter=f'metadata["document_id"] in ({document_ids})',
        )
        return results


class MilvusVectorFactory:
    def init_vdb(self, collection_name: str):
        from constants import keys

        config = MilvusConfig.model_construct(uri=keys.MILVUS_HOST_URI)
        return MilvusVector(collection_name=collection_name, config=config)


# if __name__ == "__main__":
#     print("\n=== Starting Milvus Vector Store Demo ===")

#     print("\n1. Initializing Milvus Client...")
#     config = MilvusConfig.model_construct(uri="http://127.0.0.1:19530")
#     milvs_client = MilvusVector(collection_name="test", config=config)
#     print("✓ Milvus client initialized successfully")

#     print("\n2. Loading required libraries...")
#     import os
#     import pathlib

#     from langchain_community.document_loaders import PyMuPDFLoader
#     from langchain_huggingface.embeddings import HuggingFaceEmbeddings
#     from langchain_text_splitters import RecursiveCharacterTextSplitter
#     print("✓ Libraries loaded successfully")

#     print("\n3. Initializing embedding model...")
#     embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
#     print("✓ Embedding model initialized successfully")

#     # print("\n4. Loading PDF document...")
#     # pdf_path = os.path.join(pathlib.Path(__file__).parent, 'test_data/test_contract.pdf')

#     # print(f"Loading PDF from: {pdf_path}")
#     # loader = PyMuPDFLoader(pdf_path)
#     # docs = loader.load()
#     # print(f"✓ PDF loaded successfully. Total pages: {len(docs)}")

#     # print("\n5. Splitting document into chunks...")
#     # splitter = RecursiveCharacterTextSplitter()
#     # chunks = splitter.split_documents(docs)
#     # print(f"✓ Document split into {len(chunks)} chunks")

#     # print("\n6. Extracting text content...")
#     # texts = [chunk.page_content for chunk in chunks]
#     # print(f"✓ Extracted {len(texts)} text segments")

#     # print("\n7. Generating embeddings...")
#     # embeddings = embedding_model.embed_documents(texts=texts)
#     # print(f"✓ Generated {len(embeddings)} embeddings")

#     # print("\n8. Creating document objects...")
#     # text_objs = [
#     #     Document(page_content=chunk.page_content,
#     #              vector=embedding,
#     #              metadata=chunk.metadata
#     #              )
#     #     for chunk, embedding in zip(chunks, embeddings)
#     # ]
#     # print(f"✓ Created {len(text_objs)} document objects")

#     # print("\n9. Creating collection in Milvus...")
#     # milvs_client.create(texts=text_objs, embeddings=embeddings)
#     # print("✓ Collection created successfully")

#     # print("\n=== Milvus Vector Store Demo Completed Successfully ===")
#     text = "metrics of first_call_resolution"
#     vector = embedding_model.embed_query(text)
#     results = milvs_client.search(
#             collection_name= "test",
#             data=[vector],
#             anns_field="vector",
#             limit= 4,
#             output_fields=["page_content","metadata"],
#             filter="",
#         )
#     print (results)
