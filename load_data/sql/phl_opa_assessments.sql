CREATE OR REPLACE EXTERNAL TABLE ${dataset_name}.opa_assessments(
    `parcel_number` STRING,
    `year` STRING,
    `market_value` STRING,
    `taxable_land` STRING,
    `taxable_building` STRING,
    `exempt_land` STRING,
    `exempt_building` STRING,
    `objectid` STRING
)
OPTIONS (
    format = 'JSON',
    uris = ['gs://${bucket_name}/opa_assessments/phl_opa_assessments.jsonl']
);

CREATE OR REPLACE TABLE `${internal_dataset}.opa_assessments` AS
SELECT
  *,
  parcel_number AS property_id
FROM `${dataset_name}.opa_assessments`;
