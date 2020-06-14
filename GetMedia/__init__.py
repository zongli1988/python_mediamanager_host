import logging
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, BlobProperties, generate_blob_sas, BlobSasPermissions
import azure.functions as func
from datetime import datetime, timedelta
import json
import os
import sys

from ..shared_code import auth_helper  # pylint: disable=relative-beyond-top-level
from ..shared_code import user_helper  # pylint: disable=relative-beyond-top-level
from ..shared_code import blob_helper  # pylint: disable=relative-beyond-top-level


@auth_helper.requires_auth_decorator
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    try:

        # Validate Arguments
        mediaId = req.params.get('mediaId')
        if not mediaId:
            return func.HttpResponse(
                "Please specify a mediaId",
                status_code=400
            )

        # Get content
        user_id = user_helper.getUserId(req.userInfo)
        blob_handler: blob_helper.BlobHelper = blob_helper.BlobHelper()
        container = blob_handler.getContainer(user_id)
        blobName = blob_handler.getImageBlobNameByContentId(
            user_id, mediaId, 'large')
        content = blob_handler.getContentById(user_id, mediaId)
        blob_client = container.get_blob_client(blobName)
        blob = blob_client.get_blob_properties()
        sas_token = blob_handler.generateSasToken(container, blob)

        item = {"Name": content.name, "FileName": blob.name, "Account": container.account_name,
                "Container": container.container_name, "SasToken": sas_token,
                "Content": content.__dict__}
        item["Url"] = f'https://{item["Account"]}.blob.core.windows.net/{item["Container"]}/{item["FileName"]}?{item["SasToken"]}'

        json_dump = json.dumps(item)

        return func.HttpResponse(json_dump)

    except Exception as ex:
        logging.exception('Exception:')
        logging.error(ex)
