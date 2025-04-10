import os
import pathlib
import json

import httpx
# from agents.analyze_agent import AnalyzeMetrics
from agents.analyzer2 import agent
from agents.extract_engine import ExtractionEngine
import requests
from typing import Literal
# from agents.format_agent import MetricExtractor
from agents.preprocess import PreprocessDocument
from constants import keys
from fastapi import FastAPI, Form, status
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder

from logger_config.logs import logger
from utility import utils


app = FastAPI()
upload_files_dir = os.path.join(pathlib.Path(__file__).parent.parent, "contracts")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("Application started...")


@app.get("/health_check")
def health_check():
    return {"message": "working", "status": status.HTTP_200_OK}


@app.post("/process_contract")
async def process_document(
    document_url: str = Form(...),
    document_id: str = Form(...),
    vendor_id: str = Form(...),
):
    file_name = document_url.split("/")[-1]
    object_key = document_url.split("/")
    object_key = object_key[-2] + "/" + object_key[-1]
    print (object_key)

    local_file_path = os.path.join(upload_files_dir, file_name)
    # print (document_url)
    local_contract_path = utils.download_file_content(
        bucket_name=keys.AWS_BUCKET_NAME,
        object_name=object_key,
        output_file_path=local_file_path,
    )
    # print (vendor_id)
    processer = PreprocessDocument(
        document_path=local_contract_path,
        document_id=document_id,
        collection_name= utils.serialize_uuid(vendor_id),
    )
    processer.process_document()

    return Response(
        content=f"document uploaded to vector db in collection:{vendor_id}", status_code=status.HTTP_201_CREATED
    )



async def post_data(sub_url:str, data, method:Literal['POST','PUT']):
    '''function to send data to endpoint'''

    api_endpoint_url = f"{keys.BASE_APPLICATION_URL}" + sub_url

    async with httpx.AsyncClient() as client:
        try:
            if method == "POST":
                response = await client.post(
                    api_endpoint_url,
                    json= data,
                    headers={"content-Type": "application/json"}
                )

            else:
                print ('put..........')
                response = await client.put(
                    api_endpoint_url,
                    json= data,
                    headers= {"content-Type": "application/json"}
                )
            
            return response
        
        except Exception as e:
            # raise HTTPException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST)
            print (str(e))



@app.post("/extract_target_metrics")
async def extract_target_metrics(document_id: str = Form(...), vendor_id: str = Form(...)):

    
    extractor = ExtractionEngine(document_id= document_id, collection_id= utils.serialize_uuid(vendor_id))

    results = extractor.extract()
    results_dict = jsonable_encoder(results)

    data = {"target_sla_metric": results_dict}
    
    
    sub_url = keys.BASE_APPLICATION_URL + f'contracts/{document_id}'


    headers = {'Content-Type': 'application/json'}  # Important for JSON data
    response = requests.put(sub_url, json= data, headers=headers)
    print (response)
    try:
        downstream_response = response.json()
    except Exception:
        downstream_response = response.text  # fallback if not JSON

    return Response(content= response.content, status_code= status.HTTP_200_OK)



@app.post("/analyze_metric")
async def analyze_metrics(
    target_metrics: dict,
    actual_metrics: dict,
    # vendor: dict,
    # contract: dict,
    # contract_metric: dict,
):
    results = {}
    for metric in target_metrics.keys():
        target_metric = target_metrics[metric]['result']
        actual_metric = actual_metrics[metric]

        max_value = target_metric['metric_value']['max_value']
        min_value = target_metric['metric_value'].get('min_value')
        unit = target_metric['metric_value']['data_type']
        condition = target_metric['condition']

        if min_value is not None:
            target_value = f"The target value is between min: {min_value} {unit} and max: {max_value} {unit}"
        else:
            target_value = f"The target value is: {max_value} {unit}"

        actual_value = f"{actual_metric['value']} {actual_metric['data_type']}"
        inputs = {
        "actual_metric": actual_value,
        "target_metric": target_value,
        "condition": condition,
    }
        result = agent.invoke(inputs)
        results[metric] = result

    

        
    
    # url = keys.BASE_APPLICATION_URL + "risk/"
    # async with httpx.AsyncClient() as client:
    #     try:
    #         aws_response = await client.post(
    #             url, json=data, headers={"content-Type": "application/json"}
    #         )

    #     except Exception as e:
    #         raise HTTPException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    # return Response(content=aws_response.content, status_code=aws_response.status_code)
    return results




if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
