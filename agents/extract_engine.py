from .extraction_agent2 import agent
import os
import pathlib
import json
from typing import Tuple

from logger_config.logs import logger

parent_path = pathlib.Path(__file__).parent.parent
fields_path = os.path.join(parent_path, "schema", "msa_schema.json")


if not os.path.exists(fields_path):
    raise FileExistsError


class ExtractionEngine:

    def __init__(self, document_id: str, collection_id: str):
        self.document_id = document_id
        self.collection_id = collection_id
        logger.info(f"Initialized ExtractionEngine for document_id: {document_id}, collection_id: {collection_id}")

    def get_fields(self,) -> Tuple[list]:
        try:
            logger.info("Loading fields from schema file")
            with open(fields_path, "r") as schema:
                data = json.load(schema)

            base_fields = list(data['base_fields'].keys())
            fields = list(data['metrics'].keys())
            logger.info(f"Loaded {len(base_fields)} base fields and {len(fields)} metric fields")

            return base_fields + fields, base_fields
        except FileNotFoundError:
            logger.error(f"Schema file not found at path: {fields_path}")
            raise
        except json.JSONDecodeError:
            logger.error("Invalid JSON format in schema file")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while loading fields: {str(e)}")
            raise

    def extract(self,):
        try:
            logger.info("Starting field extraction process")
            fields, base_fields = self.get_fields()
            final_fields = {}

            for field in fields:
                try:
                    logger.info(f"Processing field: {field}")
                    field_type = "base" if field in base_fields else "metric"
                    
                    result = agent.invoke({
                        "collection_id": self.collection_id,
                        "document_id": self.document_id,
                        "field_name": field,
                        "field_type": field_type
                    })
                    
                    final_fields[field] = result["result_obj"]
                    logger.info(f"Successfully processed field: {field}")
                    
                except Exception as e:
                    logger.error(f"Error processing field {field}: {str(e)}")
                    # final_fields[field] = {
                       
                    # }
                    continue

            logger.info("Field extraction completed successfully")
            return final_fields

        except Exception as e:
            logger.error(f"Critical error in extraction process: {str(e)}")
            raise

        



# e = ExtractionEngine(document_id='5f966009-e6b5-42be-b6f2-058d0d46c859', collection_id='_caa67daa_ab19_454e_8e9d_7f9b0d194dec')

# print (json.dumps(e.extract()))