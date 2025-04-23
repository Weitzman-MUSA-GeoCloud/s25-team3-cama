CREATE OR REPLACE EXTERNAL TABLE ${dataset_name}.pwd_parcels(
    `OBJECTID` STRING,
    `PARCELID` STRING,
    `TENCODE` STRING,
    `ADDRESS` STRING,
    `OWNER1` STRING,
    `OWNER2` STRING,
    `BLDG_CODE` STRING,
    `BLDG_DESC` STRING,
    `BRT_ID` STRING,
    `NUM_BRT` STRING,
    `NUM_ACCOUNTS` STRING,
    `GROSS_AREA` STRING,
    `PIN` STRING,
    `PARCEL_ID` STRING,
    `Shape__Area` STRING,
    `Shape__Length` STRING,
    `geog` STRING
)
OPTIONS (
    format = 'JSON',
    uris = ['gs://${bucket_name}/pwd_parcels/phl_pwd_parcels.jsonl']
);

CREATE OR REPLACE TABLE `${internal_dataset}.pwd_parcels` AS
SELECT
  *,
  brt_id AS property_id
FROM `${dataset_name}.pwd_parcels`;
