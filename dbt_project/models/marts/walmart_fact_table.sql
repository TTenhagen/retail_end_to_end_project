{{ config(materialized="table") }}


SELECT
    sd.store_id,
    sd.dept_id,
    dd.date_id,
    dept.weekly_sales as store_weekly_sales,
    f.fuel_price,
    f.temperature as store_temperature,
    f.unemployment,
    f.cpi,
    f.markdown1,
    f.markdown2,
    f.markdown3,
    f.markdown4,
    f.markdown5,
    sd.dbt_valid_from as vrsn_start_date,
    sd.dbt_valid_to as vrsn_end_date.
    CURRENT_TIMESTAMP() as insert_date,
    CURRENT_TIMESTAMP() as update_date
FROM {{ ref("stg_department") }} dept
JOIN {{ ref("retail_store_dim") }} sd
    ON dept.store_id = sd.store_id
    AND dept.dept_id = sd.dept_id
    AND dept.store_date BETWEEN sd.dbt_valid_from
        AND COALESCE(sd.dbt_valid_to, '9999-12-31')
JOIN {{ ref("stg_fact") }} f
    ON dept.store_id = f.store_id
    AND dept.store_date  = f.store_date
JOIN {{ ref("retail_date_dim") }} dd
    on dept.store_date = dd.store_date
;
