import logging
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, BlobProperties, generate_blob_sas, BlobSasPermissions
import azure.functions as func
from datetime import datetime, timedelta
import json


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    try:

        name = req.params.get('name')
        if not name:
            return func.HttpResponse(
                "Please specify a file name",
                status_code=400
            )
        data = req.get_body()
        if not data:
            return func.HttpResponse(
                "Please upload content",
                status_code=400
            )
        connect_str: str = 'DefaultEndpointsProtocol=https;AccountName=djbvideoappsto;AccountKey=Q2w9wi3v0JbTMUIV0kMc0K0kRHtWhTciQ4S7ZgdYSHhic59ZMQk/BlQPIFYQ/fft8uPQYymym97GgYxY4dbvOg==;EndpointSuffix=core.windows.net'

        # Create the BlobServiceClient object which will be used to create a container client
        blob_service_client = BlobServiceClient.from_connection_string(
            connect_str)

        # Create a unique name for the container
        container_name = "djbtest"

        container = blob_service_client.get_container_client(
            container_name)

        container.upload_blob(name, data,)

        return func.HttpResponse(status_code=200)

    except Exception as ex:
        logging.exception('Exception:')
        logging.error(ex)
