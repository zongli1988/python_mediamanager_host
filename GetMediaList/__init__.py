import logging
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, BlobProperties, generate_blob_sas, BlobSasPermissions
import azure.functions as func
import json
import os
from __app__.shared_code import auth_helper  # pylint: disable=import-error
from __app__.shared_code import user_helper  # pylint: disable=import-error
from __app__.shared_code import blob_helper  # pylint: disable=import-error


@auth_helper.requires_auth_decorator
def main(req: func.HttpRequest) -> func.HttpResponse:

    logging.info('Python HTTP trigger function processed a request.')
    try:

        # Ensure category specified
        category = req.params.get('category')
        if not category:
            return func.HttpResponse(
                "Please specify a category",
                status_code=400
            )

        # Get content
        user_id = user_helper.getUserId(req.userInfo)
        blob_handler: blob_helper.BlobHelper = blob_helper.BlobHelper()
        container = blob_handler.getContainer(user_id)
        content_records = blob_handler.getMatchingContent(
            user_id, category)

        ret = []
        for record in content_records:
            blob_name = record["id"] + "_thumb" + record['extension']
            blob_client = container.get_blob_client(blob_name)
            blob = blob_client.get_blob_properties()
            sas_token = blob_handler.generateSasToken(container, blob)

            item = {"Id": record["id"], "Name": record["name"], "Description": record["description"],
                    "Account": container.account_name, "FileName": blob_name,
                    "Container": container.container_name, "SasToken": sas_token,
                    "ContentType": blob.content_settings.content_type}
            item["Url"] = f'https://{item["Account"]}.blob.core.windows.net/{item["Container"]}/{item["FileName"]}?{item["SasToken"]}'

            ret.append(item)

        json_dump = json.dumps(ret)
        return func.HttpResponse(json_dump)

    except Exception as ex:
        logging.exception('Exception:')
        logging.info(ex)
        logging.error(ex)
