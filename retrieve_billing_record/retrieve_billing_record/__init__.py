import logging
import azure.functions as func
import json
from azure.cosmos import CosmosClient, exceptions
from azure.storage.blob import BlobServiceClient

COSMOS_URL = "<your_cosmos_endpoint>"
COSMOS_KEY = "<your_cosmos_key>"
COSMOS_DB = "billing-db"
COSMOS_CONTAINER = "records"

BLOB_CONN_STR = "<your_blob_connection_string>"
BLOB_CONTAINER = "billing-archive"

def find_blob_path(record_id):
    # If using deterministic naming, try all year/month/day folders (or index)
    # Here we mock that logic assuming 1 folder per record_id hash
    return f"{record_id[:4]}/{record_id}.json"

def main(req: func.HttpRequest) -> func.HttpResponse:
    record_id = req.route_params.get('record_id')
    partition_key = req.params.get('partitionKey')

    if not record_id or not partition_key:
        return func.HttpResponse("Missing 'record_id' or 'partitionKey'", status_code=400)

    try:
        cosmos_client = CosmosClient(COSMOS_URL, COSMOS_KEY)
        container = cosmos_client.get_database_client(COSMOS_DB).get_container_client(COSMOS_CONTAINER)
        item = container.read_item(record_id, partition_key)
        return func.HttpResponse(json.dumps(item), mimetype="application/json")
    except exceptions.CosmosResourceNotFoundError:
        # Fallback to Blob Storage
        blob_service = BlobServiceClient.from_connection_string(BLOB_CONN_STR)
        archive_container = blob_service.get_container_client(BLOB_CONTAINER)
        blob_path = find_blob_path(record_id)

        try:
            blob_client = archive_container.get_blob_client(blob_path)
            blob_data = blob_client.download_blob().readall()
            return func.HttpResponse(blob_data, mimetype="application/json")
        except Exception as e:
            return func.HttpResponse(f"Record not found in archive. Error: {str(e)}", status_code=404)
