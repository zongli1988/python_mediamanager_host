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
        articleId = req.params.get('id')
        if not articleId:
            return func.HttpResponse(
                "Please specify a articleId",
                status_code=400
            )

        # Get content
        user_id = user_helper.getUserId(req.userInfo)
        blob_handler: blob_helper.BlobHelper = blob_helper.BlobHelper()
        container = blob_handler.getContainer(user_id)
        content = blob_handler.getContentById(user_id, articleId)
        if content.content_type != "text/plain":
            return func.HttpResponse(
                "Content item is not an article",
                status_code=400
            )
        blobName = blob_handler.getBlobNameByContentId(
            user_id, articleId, None)

        blob_client = container.get_blob_client(blobName)
        data_stream = blob_client.download_blob()
        data = data_stream.readall()
        # blob = blob_client.get_blob_properties()
        # sas_token = blob_handler.generateSasToken(container, blob)

        # item = {"Name": content.name, "FileName": blob.name, "Account": container.account_name,
        #         "Container": container.container_name, "SasToken": sas_token,
        #         "Content": content.__dict__}
        # item["Url"] = f'https://{item["Account"]}.blob.core.windows.net/{item["Container"]}/{item["FileName"]}?{item["SasToken"]}'

        # json_dump = json.dumps(item)

        return func.HttpResponse(data)

    except Exception as ex:
        logging.exception('Exception:')
        logging.error(ex)
