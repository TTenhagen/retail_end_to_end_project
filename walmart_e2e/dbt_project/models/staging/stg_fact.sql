SELECT
    CAST(store as int) as store_id,
    CAST(date as DATE) as store_date,
    CAST(temperature as decimal(10,4)) as temperature,
    CAST(fuel_price as decimal(10,4)) as fuel_price,
    CAST(markdown1 as decimal(14,2)) as markdown1,
    CAST(markdown2 as decimal(14,2)) as markdown2,
    CAST(markdown3 as decimal(14,2)) as markdown3,
    CAST(markdown4 as decimal(14,2)) as markdown4,
    CAST(markdown5 as decimal(14,2)) as markdown5,
    CAST(cpi as decimal(14,6)) as cpi,
    CAST(unemployment as decimal(10,4)) as unemployment,
    CAST(isholiday as boolean) as is_holiday
FROM {
    {
        source("bronze", "fact_raw")
    }
}
;