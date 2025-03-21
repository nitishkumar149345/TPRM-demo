import os
import pathlib

from agents.format_agent import MetricExtractor
from fastapi import FastAPI, File, Form, UploadFile, WebSocket, status
from fastapi.exceptions import HTTPException
from fastapi.responses import Response, StreamingResponse
from utility import utils

from .websocket_manager import WebSocketManager

app = FastAPI()
upload_files_dir = os.path.join(pathlib.Path(__file__).parent.parent, 'contracts')


@app.get('/health_check')
def health_check(request,):
    return Response({"message":"working","status":status.HTTP_200_OK})



# @app.post('/extract')
# def extract_document(request, file_url:str = Form(...)):


@app.post('/process_contract')
def extract_contract(request, file_url: str = Form(...)):

    extractor = MetricExtractor(file_path= file_url)
    results = extractor.process_metrics()

    return results

@app.post('/process_contract1')
async def extract(file: UploadFile = File(...)):

    file_name = file.filename
    file_path = os.path.join(upload_files_dir, file_name)
    
    with open( file_path, "wb") as buffer:
        buffer.write(await file.read())

    
    extractor = MetricExtractor(file_path= file_path)
    results = extractor.process_metrics()
    return results



if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app)


    
