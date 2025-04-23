from dotenv import load_dotenv
load_dotenv()

# import csv
import json
import os
import pathlib

import pyproj
from shapely import wkt
import functions_framework
from google.cloud import storage

PREPARED_DATA_DIR = pathlib.Path(__file__).parent


@functions_framework.http
def prepare_phl_pwd_parcels(request):
    print('Preparing PWD Parcels data...')

    raw_filename = PREPARED_DATA_DIR / 'phl_pwd_parcels.geojson'
    prepared_filename = PREPARED_DATA_DIR / 'phl_pwd_parcels.jsonl'

    bucket_name = os.getenv('RAW_DATA_BUCKET')
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # Download the data from the bucket
    raw_blobname = 'pwd_parcels/phl_pwd_parcels.geojson'
    blob = bucket.blob(raw_blobname)
    blob.download_to_filename(raw_filename)
    print(f'Downloaded to {raw_filename}')

    # Load the data from the geojson file
    with open(raw_filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Set up the projection
    transformer = pyproj.Transformer.from_proj('epsg:2272', 'epsg:4326')

    # Write the data to a JSONL file
    with open(prepared_filename, 'w') as f:
        for feature in data['features']:
            row = feature['properties']
            row['geog'] = (
                json.dumps(feature['geometry'])
                if feature['geometry'] and feature['geometry']['coordinates']
                else None
            )
            f.write(json.dumps(row) + '\n')

    print(f'Processed data into {prepared_filename}')

    # Upload the prepared data to the bucket
    bucket_name = os.getenv('PREPARE_DATA_BUCKET')
    bucket = storage_client.bucket(bucket_name)
    prepared_blobname = 'pwd_parcels/phl_pwd_parcels.jsonl'
    blob = bucket.blob(prepared_blobname)
    blob.upload_from_filename(prepared_filename)
    print(f'Uploaded to {prepared_blobname}')

    return f'Processed data into {prepared_filename} and uploaded to gs://{bucket_name}/{prepared_blobname}'
