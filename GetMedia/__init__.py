import logging
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, BlobProperties, generate_blob_sas, BlobSasPermissions
import azure.functions as func
from datetime import datetime, timedelta
import json
import os
from __app__.shared_code import auth_helper  # pylint: disable=import-error
from __app__.shared_code import user_helper  # pylint: disable=import-error
from __app__.shared_code import blob_helper  # pylint: disable=import-error


@auth_helper.requires_auth_decorator
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    try:

        # Validate Arguments
        name = req.params.get('name')
        if not name:
            return func.HttpResponse(
                "Please specify a category",
                status_code=400
            )

        # Get content
        user_id = user_helper.getUserId(req.userInfo)
        blob_handler: blob_helper.BlobHelper = blob_helper.BlobHelper()
        container = blob_handler.getContainer(user_id)
        blob_client = container.get_blob_client(name)
        blob = blob_client.get_blob_properties()
        sas_token = blob_handler.generateSasToken(container, blob)

        ret = {"Name": blob.name, "Account": container.account_name,
               "Container": container.container_name, "SasToken": sas_token}
        json_dump = json.dumps(ret)

        return func.HttpResponse(json_dump)

    except Exception as ex:
        logging.exception('Exception:')
        logging.error(ex)
