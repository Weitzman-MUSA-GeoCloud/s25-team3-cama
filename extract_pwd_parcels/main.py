from dotenv import load_dotenv
load_dotenv()

import os
import pathlib
import requests
import functions_framework
from google.cloud import storage

DATA_DIR = pathlib.Path(__file__).parent 

@functions_framework.http
def extract_phl_pwd_parcels(request):
    print('Extracting PHL PWD Parcels data...')

    # Download the PWD Parcels data as a geojson
    url = 'https://opendata.arcgis.com/datasets/84baed491de44f539889f2af178ad85c_0.geojson'
    filename = DATA_DIR / 'phl_pwd_parcels.geojson'

    response = requests.get(url)
    response.raise_for_status()

    with open(filename, 'wb') as f:
        f.write(response.content)

    print(f'Downloaded {filename}')

    # Upload the downloaded file to cloud storage
    BUCKET_NAME = os.getenv('RAW_DATA_BUCKET')
    blobname = 'pwd_parcels/phl_pwd_parcels.geojson'

    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(blobname)
    blob.upload_from_filename(filename)

    print(f'Upload {blobname} to {BUCKET_NAME}')

    return f'Downloaded and uploaded gs://{BUCKET_NAME}/{blobname}'