{% snapshot walmart_store_dim %}

{{ 
    config(
        target_schema = "walmart_gold",
        unique_key = "store_id || dept_id",
        strategy = "check",
        check_cols = ["store_type", "store_size"],
        invalidate_hard_deletes = True
        )
}}

SELECT
    s.store_id,
    d.dept_id,
    s.store_type,
    s.store_size,
    CURRENT_TIMESTAMP() as insert_date,
    CURRENT_TIMESTAMP() as update_date
FROM {{ ref("stg_strores")}} s
CROSS JOIN (SELECT DISTINCT dept_id FROM {{ ref("stg_department")}}) d
;


{% endsnapshot %}