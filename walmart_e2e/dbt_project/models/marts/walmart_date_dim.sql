{{ config(materialized="table", unique_key="date_id")}}

SELECT
    ROW_NUMBER() OVER (ORDER BY store_date) as date_id,
    store_id,
    is_holiday,
    CURRENT_TIMESTAMP() as insert_date,
    CURRENT_TIMESTAMP() as update_date
FROM(
    SELECT DISTINCT store_date, is_holiday
    FROM {{ ref("stg_fact") }}
)
;