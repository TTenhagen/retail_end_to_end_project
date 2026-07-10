SELECT
    CAST(store as int) as store_id,
    CAST(dept as int) as dept_id,
    CAST(date as date) as store_date,
    CAST(weekly_sales as decimal(14,2)) as weekly_sales,
    CAST(isholiday as boolean) as is_holiday
FROM {
    {
        source("bronze", "department_raw")
    }
}
WHERE weekly_sales IS NOT NULL
;