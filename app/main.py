import os
import pathlib
from io import BytesIO
import httpx
# from agents.analyze_agent import AnalyzeMetrics
from agents.analyzer2 import agent
from agents.extract_engine import ExtractionEngine
import requests
from typing import Literal
# from agents.format_agent import MetricExtractor
from agents.preprocess import PreprocessDocument
from constants import keys
from fastapi import FastAPI, Form, status, File, UploadFile
# from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.encoders import jsonable_encoder

from logger_config.logs import logger
from utility import utils
import pandas as pd

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
    file_name, object_key = utils.parse_s3_url(document_url)
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
    
    return Response(content= response.content, status_code= status.HTTP_200_OK)


def is_schema_output(response):
    return (
        isinstance(response, dict)
        and 'properties' in response
        and '$defs' in response
        and 'actual_metric' in response
        and 'target_metric' in response
    )



@app.post("/process_actual_metrics")
async def process_actual_metrics(file:UploadFile = File(...)):


    # file_object = file.filename
    data = await file.read()
    dataframe = pd.read_excel(BytesIO(data), engine="openpyxl")
    # print(dataframe)

    vendor_id = dataframe.iloc[1,1]
    contract_id = dataframe.iloc[2,1]
    dataframe.fillna(0, inplace=True)

    actual_metric_data = {
        row[0]: {"value": row[1], "data_type": row[2]} 
        for index, row in dataframe.iterrows() if index >=6 
    }

    payload = {
        "vendor_id": vendor_id,
        "contract_id": contract_id,
        "frequency": 'monthly',
        "actual_metric": actual_metric_data
    }
    

    sub_url = keys.BASE_APPLICATION_URL + '/metrics/'
    headers = {'Content-Type': 'application/json'}  
    response = requests.post(sub_url, json= payload, headers=headers)

    return Response(content= response.content, status_code= status.HTTP_200_OK) 
    # return payload


@app.post("/analyze_metric")
async def analyze_metrics(
    target_metrics: dict,
    actual_metrics: dict,
    vendor: dict,
    contract: dict,
    contract_metric: dict,
):
    

    vendor_id = vendor['vendor_id']
    contract_id = contract['contract_id']
    actual_metric_id = contract_metric['actual_metric_id']

    results = {}
    for metric in target_metrics.keys():
        target_metric = target_metrics[metric]
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

        # print (result)
        # print (type(result) ,result.get('properties'))

        if 'properties' in result.keys():
            print (f'Got invalid output, reinvoking metric:{metric}')
            result = agent.invoke(inputs)

        results[metric] = result['result_obj']
        results[metric]['actual_metric'] = actual_metric
        results[metric]['target_metric'] = target_metric['metric_value']
        results[metric]['condition'] = condition


    # print (results)
    url = keys.BASE_APPLICATION_URL + 'risk/'
    results = jsonable_encoder(results)

    data = {
        "vendor_id": vendor_id,
        "contract_id": contract_id,
        "contract_metric_id": actual_metric_id,
        "risk_comparison": results
    }

    try:
        response = requests.post(
            url,
            json= data,
            headers= {'Content-Type': 'application/json'}
        )
    except Exception:
        raise Exception

    return Response(content= response.content, status_code= status.HTTP_200_OK)




if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
