import logging
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, BlobProperties, generate_blob_sas, BlobSasPermissions
import azure.functions as func
from datetime import datetime, timedelta
import json
import os
from azure.cosmosdb.table.tableservice import TableService
from azure.cosmosdb.table.models import Entity


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

            # TODO: Set user id based on authentication
            content_records = getMatchingContent(
                "bfcc42bc-259d-42dc-bff6-dafda26ea22b", 'NO CATEGORY YET')
            # blobs = container.list_blobs()

            ret = []
            # for blob in blobs:

            #     logging.info(blob.name)
            for record in content_records:
                blob_name = record["id"] + "_thumb" + record['extension']
                blob_client = container.get_blob_client(
                    blob_name)
                blob = blob_client.get_blob_properties()
                sas_token = generate_blob_sas(
                    container.account_name,
                    container.container_name,
                    blob.name,
                    account_key=blob_service_client.credential.account_key,
                    permission=BlobSasPermissions(read=True),
                    expiry=datetime.utcnow() + timedelta(hours=1))

                video = {"Id": record["id"], "Name": record["name"], "Description": record["description"], "Account": container.account_name,
                         "Container": container.container_name, "SasToken": sas_token, "ContentType": blob.content_settings.content_type}

                ret.append(video)

            json_dump = json.dumps(ret)

            print(json_dump)
            return func.HttpResponse(json_dump)

        else:
            return func.HttpResponse(
                "Please specify a category",
                status_code=400
            )

    except Exception as ex:
        logging.exception('Exception:')
        logging.info(ex)
        logging.error(ex)


def getMatchingContent(user_id: str, category: str):
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
