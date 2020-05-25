import logging
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, BlobProperties, ContentSettings, generate_blob_sas, BlobSasPermissions
import azure.functions as func
from datetime import datetime, timedelta
import json
import os
import io
import PIL
from PIL import Image, ExifTags


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

        # Gather metadata and content types etc.
        contentType = req.headers.get("Content-Type")

        # Connect to blob storage
        connect_str = os.environ["StorageConnectionString"]
        blob_service_client = BlobServiceClient.from_connection_string(
            connect_str)
        container_name = "djbtest"
        container = blob_service_client.get_container_client(
            container_name)

        # Thumbnail Image
        saveMedia(data, (500, 500), name, "thumbnail",
                  container, contentType)

        # Save Large Image
        saveMedia(data, (1200, 1200), name, "large",
                  container, contentType)

        # Save Original Image
        saveMedia(data, None, name, "original",
                  container, contentType)

        return func.HttpResponse(status_code=200)

    except Exception as ex:
        logging.exception('Exception:')
        logging.error(ex)


def saveMedia(data, size, name, sizeName, container: ContainerClient, contentType: str):
    byteArr = data
    if contentType.lower().startswith("image") and size != None:  # Only convert if required
        byteArr = convertImage(data, size)
    metadata: dict(str, str) = {"SizeName": sizeName}
    content_settings = ContentSettings(content_type=contentType)
    filename = convertFileName(name, sizeName)
    container.upload_blob(
        filename, byteArr, content_settings=content_settings, metadata=metadata)


def convertImage(imageData, size=(500, 500)):
    smallData = Image.open(io.BytesIO(imageData))
    for orientation in ExifTags.TAGS.keys():
        if ExifTags.TAGS[orientation] == 'Orientation':
            break
    exif = dict(smallData._getexif().items())
    imageFormat = smallData.format
    if exif[orientation] == 3:
        smallData = smallData.rotate(180, expand=True)
    elif exif[orientation] == 6:
        smallData = smallData.rotate(270, expand=True)
    elif exif[orientation] == 8:
        smallData = smallData.rotate(90, expand=True)
    smallData.thumbnail(size, Image.ANTIALIAS)
    byteIO = io.BytesIO()
    smallData.save(byteIO, format=imageFormat)
    byteArr = byteIO.getvalue()
    return byteArr


def convertFileName(name, version):
    filename, file_extension = os.path.splitext(name)
    filename = filename + "_" + version + file_extension
    return filename
