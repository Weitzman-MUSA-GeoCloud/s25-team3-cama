from dotenv import load_dotenv
load_dotenv()

import csv
import json
import os
import pathlib

import pyproj
from shapely import wkt
import functions_framework
from google.cloud import storage

DIRNAME = pathlib.Path(__file__).parent


@functions_framework.http
def prepare_phl_opa_assessments(request):
    print('Preparing OPA Assessments data...')

    raw_filename = DIRNAME / 'phl_opa_assessments.csv'
    prepared_filename = DIRNAME / 'phl_opa_assessments.jsonl'

    bucket_name = os.getenv('RAW_DATA_BUCKET')
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # Download the data from the bucket
    raw_blobname = 'opa_assessments/phl_opa_assessments.csv'
    blob = bucket.blob(raw_blobname)
    blob.download_to_filename(raw_filename)
    print(f'Downloaded to {raw_filename}')

    # Load the data from the CSV file
    with open(raw_filename, 'r') as f:
        reader = csv.DictReader(f)
        data = list(reader)

    # Read CSV and write to JSONL
    with open(raw_filename, 'r') as infile, open(prepared_filename, 'w') as outfile:
        reader = csv.DictReader(infile)
        for row in reader:
            json_line = json.dumps(row)
            outfile.write(json_line + '\n')

    print(f'Processed data into {prepared_filename}')

    # Upload the prepared data to the bucket
    bucket_name = os.getenv('PREPARE_DATA_BUCKET')
    bucket = storage_client.bucket(bucket_name)
    prepared_blobname = 'opa_assessments/phl_opa_assessments.jsonl'
    blob = bucket.blob(prepared_blobname)
    blob.upload_from_filename(prepared_filename)
    print(f'Uploaded to {prepared_blobname}')

    return f'Processed data into {prepared_filename} and uploaded to gs://{bucket_name}/{prepared_blobname}'
