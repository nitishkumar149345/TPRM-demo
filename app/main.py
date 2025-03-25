import os
import pathlib

import httpx
from agents.format_agent import MetricExtractor
from agents.analyze_agent import AnalyzeMetrics
from fastapi import FastAPI, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from fastapi.responses import Response  # ,StreamingResponse, RedirectResponse
from utility import utils
from constants import keys
from logger_config.logs import logger
# from .websocket_manager import WebSocketManager

app = FastAPI()
upload_files_dir = os.path.join(pathlib.Path(__file__).parent.parent, "contracts")



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info('Application started...')

@app.get("/health_check")
def health_check():
    return {"message": "working", "status": status.HTTP_200_OK}



@app.post("/process_contract")
async def extract(contract_url:str = Form(...), contract_id: str = Form(...)):
    

    file_name = contract_url.split('/')[-1]
    local_file_path = os.path.join(upload_files_dir, file_name)
    local_contract_path = utils.download_file_content(bucket_name= keys.AWS_BUCKET_NAME, 
                                                      object_name= contract_url,
                                                      output_file_path= local_file_path)
    
    # print (local_contract_path)

    url = {keys.BASE_APPLICATION_URL} + f"contracts/{contract_id}"
    extractor = MetricExtractor(file_path= local_contract_path)
    results = extractor.process_metrics()
  
    results = {"target_sla_metric": results}

    async with httpx.AsyncClient() as client:
        try:
            aws_response = await client.put(
                url, json=results, headers={"content-Type": "application/json"}
            )

        except Exception as e:
            raise HTTPException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    # return local_contract_path
    return Response(content=aws_response.content, status_code=aws_response.status_code)



@app.post('/analyze_metric')
async def analyze_metrics(target_metrics: dict, actual_metrics:dict, vendor:dict, contract:dict, contract_metric:dict):
    
    analyzer = AnalyzeMetrics(
        target_metrics= target_metrics,
        actual_metrics= actual_metrics
    )
    results = analyzer.analyze()
    # from rich import print
    # print (results)
    data = {
        "vendor_id":vendor['vendor_id'],
        "contract_id":contract['contract_id'],
        "contract_metric_id":contract_metric['contract_metric_id'],
        "risk_comparison":results
    }

    url = keys.BASE_APPLICATION_URL + "risk/"
    async with httpx.AsyncClient() as client:
        try:
            aws_response = await client.post(
                url, json=data, headers={"content-Type": "application/json"}
            )

        except Exception as e:
            raise HTTPException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    # return results
    return Response(content=aws_response.content, status_code=aws_response.status_code)



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
