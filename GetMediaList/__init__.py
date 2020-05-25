import logging
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, BlobProperties, generate_blob_sas, BlobSasPermissions
import azure.functions as func
from datetime import datetime, timedelta
import json
import os


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    try:

        category = req.params.get('category')
        if not category:
            try:
                req_body = req.get_json()
            except ValueError:
                pass
            else:
                category = req_body.get('category')

        if category:
            connect_str = os.environ["StorageConnectionString"]

            # Create the BlobServiceClient object which will be used to create a container client
            blob_service_client = BlobServiceClient.from_connection_string(
                connect_str)

            # Create a unique name for the container
            container_name = "djbtest"

            container = blob_service_client.get_container_client(
                container_name)

            blobs = container.list_blobs()

            ret = []
            for blob in blobs:

                logging.info(blob.name)
                sas_token = generate_blob_sas(
                    container.account_name,
                    container.container_name,
                    blob.name,
                    account_key=blob_service_client.credential.account_key,
                    permission=BlobSasPermissions(read=True),
                    expiry=datetime.utcnow() + timedelta(hours=1))

                video = {"Name": blob.name, "Account": container.account_name,
                         "Container": container.container_name, "SasToken": sas_token, "ContentType": blob.content_settings.content_type}

                ret.append(video)

            json_dump = json.dumps(ret)

            print(json_dump)
            return func.HttpResponse(json_dump)

        else:
            return func.HttpResponse(
                "https://www.google.com/logos/doodles/2020/israel-kamakawiwooles-61st-birthday-6753651837108391.2-s.png",
                status_code=200
            )

    except Exception as ex:
        logging.exception('Exception:')
        logging.info(ex)
        logging.error(ex)
