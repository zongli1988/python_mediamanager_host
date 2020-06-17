import logging
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, BlobProperties, ContentSettings, generate_blob_sas, BlobSasPermissions
import azure.functions as func
from datetime import datetime, timedelta
import json
import os
import io
import PIL
from PIL import Image, ExifTags
from azure.cosmosdb.table.tableservice import TableService
from azure.cosmosdb.table.models import Entity
import uuid

from __app__.shared_code import auth_helper  # pylint: disable=import-error
from __app__.shared_code import user_helper  # pylint: disable=import-error
from __app__.shared_code import blob_helper  # pylint: disable=import-error


@auth_helper.requires_auth_decorator
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    try:

        # Validate arguments
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

        # Gather metadata and content types etc.
        contentType: str = req.headers.get("Content-Type")

        # Get content
        user_id = user_helper.getUserId(req.userInfo)
        blob_handler: blob_helper.BlobHelper = blob_helper.BlobHelper()
        container = blob_handler.getContainer(user_id)

        content_id = blob_handler.createContentRecord(
            user_id, name, contentType)

        if contentType.lower() == "image/jpeg":

            # Save Image
            blob_handler.saveImage(
                data, content_id, name, container, contentType)
        elif contentType.lower() == "text/plain":
            blob_handler.saveFile(data, content_id, content_id + '.txt',
                                  container, None, contentType)
        else:
            return func.HttpResponse(
                "Unknown content type",
                status_code=400
            )

        result = {
            "Id": content_id
        }
        json_result = json.dumps(result)

        return func.HttpResponse(json_result, status_code=201)

    except Exception as ex:
        logging.exception('Exception:')
        logging.error(ex)
