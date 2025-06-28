# Timer-triggered Azure Function (e.g., daily)
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient
from datetime import datetime, timedelta
import json

def archive_old_records():
    cutoff_date = datetime.utcnow() - timedelta(days=90)

    cosmos_client = CosmosClient(url, key)
    blob_service = BlobServiceClient.from_connection_string(blob_conn_str)

    container = cosmos_client.get_database_client('billing').get_container_client('records')
    archive_container = blob_service.get_container_client("billing-archive")

    query = f"SELECT * FROM c WHERE c.timestamp < '{cutoff_date.isoformat()}'"
    for record in container.query_items(query, enable_cross_partition_query=True):
        blob_name = f"{record['timestamp'][:10].replace('-', '/')}/{record['id']}.json"
        archive_container.upload_blob(blob_name, json.dumps(record), overwrite=True)

        container.delete_item(record, partition_key=record['partitionKey'])
