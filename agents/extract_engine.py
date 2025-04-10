from .extraction_agent2 import agent
import os
import pathlib
import json
from typing import Tuple



parent_path = pathlib.Path(__file__).parent.parent
fields_path = os.path.join(parent_path, "schema", "msa_schema.json")


if not os.path.exists(fields_path):
    raise FileExistsError


class ExtractionEngine:

    def __init__(self, document_id: str, collection_id: str):
        self.document_id = document_id
        self.collection_id = collection_id



    def get_fields(self,) -> Tuple[list]:

        with open(fields_path, "r")as schema:
            data = json.load(schema)

        base_fields = list(data['base_fields'].keys())
        fields = list(data['metrics'].keys())

        return base_fields + fields, base_fields
    

    def extract(self,):
        
        fields, base_fields = self.get_fields()
        final_fields = {}

        for field in fields:
            if field in base_fields:
                result = agent.invoke({
                    "collection_id": self.collection_id,
                    "document_id": self.document_id,
                    "field_name": field,
                    "field_type": "base"
                })
            else:
                result = agent.invoke({
                    "collection_id": self.collection_id,
                    "document_id": self.document_id,
                    "field_name": field,
                    "field_type": "metric"
                })

            final_fields[field] = result["result_obj"]

        return final_fields

        



# e = ExtractionEngine(document_id='5f966009-e6b5-42be-b6f2-058d0d46c859', collection_id='_caa67daa_ab19_454e_8e9d_7f9b0d194dec')

# print (json.dumps(e.extract()))