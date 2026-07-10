SELECT
    CAST (store as int) as store_id,
    TRIM(type) as store_type,
    CAST(size as int) as store_size
FROM {{source{"walmart_bronze", "stores_raw"}}}
;