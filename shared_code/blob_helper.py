from azure.storage.blob import BlobServiceClient, ContentSettings, BlobClient, ContainerClient, BlobProperties, generate_blob_sas, BlobSasPermissions
import json
import os
import io
from azure.cosmosdb.table.tableservice import TableService
from azure.cosmosdb.table.models import Entity
from datetime import datetime, timedelta
import uuid
import PIL
from PIL import Image, ExifTags


class BlobHelper:

    def __init__(self):
        self.blob_service_client = self.getBlobServiceClient()

    def getBlobServiceClient(self):
        connect_str = os.environ["StorageConnectionString"]

        # Create the BlobServiceClient object which will be used to create a container client
        return BlobServiceClient.from_connection_string(connect_str)

    def getContainer(self, user_id):

        container_name = user_id
        container = self.blob_service_client.get_container_client(
            container_name)

        # Create the container if it doesn't exist
        try:
            container.get_container_properties()
        except Exception:
            container.create_container()

        return container

    def getMatchingContent(self, user_id: str, category: str) -> list:
        account_name = os.environ["StorageAccountName"]
        account_key = os.environ["StorageAccountKey"]
        table_service = TableService(
            account_name=account_name, account_key=account_key)
        filterString = "PartitionKey eq '" + user_id + "'"
        content_items = table_service.query_entities(
            'content', filter=filterString)
        results = []
        for content in content_items:
            results.append({"id": content.RowKey,
                            "extension": content.Extension,
                            "name": content.Name,
                            "description": (content.Description if "Description" in content else "")})
        return results

    def generateSasToken(self, container: ContainerClient, blob: BlobProperties) -> str:
        sas_token = generate_blob_sas(
            container.account_name,
            container.container_name,
            blob.name,
            account_key=self.blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=1))
        return sas_token

    def createContentRecord(self, user_id: str, filename: str, content_type: str):
        account_name = os.environ["StorageAccountName"]
        account_key = os.environ["StorageAccountKey"]
        table_service = TableService(
            account_name=account_name, account_key=account_key)
        record_id = str(uuid.uuid4())
        name, file_extension = os.path.splitext(filename)
        record = {'PartitionKey': user_id, 'RowKey': record_id, 'Name': name,
                  'ContentType': content_type, "Extension": file_extension, 'FileName': filename}
        table_service.insert_entity('content', record)
        return record_id

    def saveMedia(self, data, size, content_id: str, name: str, sizeName: str, container: ContainerClient, contentType: str):
        byteArr = data
        if contentType.lower().startswith("image") and size != None:  # Only convert if required
            byteArr = self.convertImage(data, size)
        metadata: dict(str, str) = {"SizeName": sizeName}
        content_settings = ContentSettings(content_type=contentType)
        filename = self.convertFileName(name, content_id, sizeName)
        container.upload_blob(
            filename, byteArr, content_settings=content_settings, metadata=metadata)

    def convertImage(self, imageData, size=(500, 500)):
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

    def convertFileName(self, name, content_id, version):
        filename, file_extension = os.path.splitext(name)
        filename = content_id + "_" + version + file_extension
        return filename
