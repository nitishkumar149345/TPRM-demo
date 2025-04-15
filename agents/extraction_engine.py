from .extraction_agent3 import summarizer, formatter, output_parser
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
        
        logger.info("Starting field extraction process")
        fields, base_fields = self.get_fields()
        final_fields = {}

        summarizing_agent = summarizer(collection_id= self.collection_id, document_id= self.document_id)
        formatting_agent = formatter()
        format_instructions = output_parser.get_format_instructions()

        for field in fields:
            if field not in base_fields:
                query = f'Identify numerical threshold (max and min values), their data type, condition and frequency of KPI metric: {field}, and summarize'
                try:
                    logger.info(f"Processing field: {field}")
                    summary = summarizing_agent.invoke({
                        "input":query
                    })

                    result = formatting_agent.invoke({
                        "input":f'Interpret this text summary:{summary} of {field}, into specified json format.',
                        "format_instructions": format_instructions
                    })

                    final_fields[field] = result
                    logger.info(f"Successfully processed field: {field}")
                except Exception as e:
                    raise Exception(e)

        return final_fields