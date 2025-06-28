def get_billing_record(record_id):
    try:
        # Primary read from Cosmos DB
        record = cosmos_container.read_item(record_id, partition_key)
        return record
    except NotFoundError:
        # Fallback to Blob Storage
        blob_path = find_archive_path(record_id)  # e.g., via Azure Table or naming logic
        blob_client = archive_container.get_blob_client(blob_path)
        blob_data = blob_client.download_blob().readall()
        return json.loads(blob_data)
