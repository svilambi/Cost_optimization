import datetime
import json
import logging
import azure.functions as func
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient

COSMOS_URL = "<your_cosmos_endpoint>"
COSMOS_KEY = "<your_cosmos_key>"
COSMOS_DB = "billing-db"
COSMOS_CONTAINER = "records"

BLOB_CONN_STR = "<your_blob_connection_string>"
BLOB_CONTAINER = "billing-archive"

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    logging.info('Archival function triggered at %s', utc_timestamp)

    cosmos_client = CosmosClient(COSMOS_URL, COSMOS_KEY)
    container = cosmos_client.get_database_client(COSMOS_DB).get_container_client(COSMOS_CONTAINER)

    blob_service = BlobServiceClient.from_connection_string(BLOB_CONN_STR)
    archive_container = blob_service.get_container_client(BLOB_CONTAINER)

    cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=90)
    query = f"SELECT * FROM c WHERE c.timestamp < '{cutoff_date.isoformat()}'"

    for item in container.query_items(query, enable_cross_partition_query=True):
        partition_key = item['partitionKey']
        record_id = item['id']
        date_str = item['timestamp'][:10].replace('-', '/')
        blob_name = f"{date_str}/{record_id}.json"
        
        archive_container.upload_blob(name=blob_name, data=json.dumps(item), overwrite=True)
        container.delete_item(item=record_id, partition_key=partition_key)

    logging.info("Archival process completed.")
