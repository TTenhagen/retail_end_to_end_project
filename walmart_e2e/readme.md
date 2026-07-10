🛒 Walmart Retail Sales Analytics

End-to-end Medallion-architecture data pipeline transforming raw weekly sales data into a governed, query-ready dimensional model — with a Python visualization layer querying the warehouse directly.


📋 Overview

Walmart needs a single source of truth for weekly sales performance across stores and departments — one that accounts for seasonality, holiday effects, regional economic conditions, and promotional markdowns. This project builds that source of truth from three flat source files into a fully governed Snowflake warehouse, then delivers the 10 specific business reports stakeholders asked for, generated directly in Python with no BI tool dependency.

The numbers:

421,570 weekly department-sales records
45 stores across 3 store types (A / B / C)
3 years of history (2010–2012), including fuel price, CPI, and unemployment as external signals
10 required business reports, each reproducible with a single Python script run



🏗️ Architecture

┌─────────────┐     ┌──────────────┐     ┌─────────────────────────────────┐     ┌────────────────┐
│  Local CSVs │ ──▶ │   AWS S3     │ ──▶│         SNOWFLAKE              │ ──▶ │  Python Charts  │
│  (3 files)  │     │ (raw landing)│     │  Bronze → Silver → Gold (dbt)   │     │ (matplotlib/sns)│
└─────────────┘     └──────────────┘     └─────────────────────────────────┘     └────────────────┘
                                                   ▲
                                          dbt Cloud orchestrates
                                       staging views + SCD1/SCD2 models

LayerTechnologyPurposeIngestionPython + boto3Uploads raw CSVs to S3 with deterministic, idempotent file pathsRaw StorageAWS S3Landing zone, source of truth for re-processingWarehouseSnowflakeExternal stage + COPY INTO for Bronze load, NULL_IF handling for malformed markdown fieldsTransformationdbt CloudSilver staging views (typed/cleaned) → Gold dimensional model (SCD1 date dim, SCD2 store dim via dbt snapshot)VisualizationPython (snowflake-connector-python, matplotlib, seaborn)Queries Gold schema directly, renders 10 publication-ready PNGs


🗂️ Data Model

Gold layer — star schema:

                         WALMART_DATE_DIM (SCD1)
                                 │
                                 ▼
WALMART_STORE_DIM ──▶ WALMART_FACT_TABLE ◀── (sales, markdowns, weather, CPI)
   (SCD2, dbt
    snapshot)


WALMART_DATE_DIM — one row per calendar date, holiday flag (SCD1: simple upsert)
WALMART_STORE_DIM — store type, size, tracked historically via dbt snapshot (SCD2: dbt_valid_from / dbt_valid_to)
WALMART_FACT_TABLE — weekly sales joined to weather, fuel price, CPI, unemployment, and 5 markdown columns



📊 The 10 Reports

#ReportChart Type1Weekly Sales by Store & HolidayGrouped bar2Weekly Sales by Temperature & YearGrouped bar (binned)3Weekly Sales by Store SizeFilled area4Weekly Sales by Store Type & MonthMulti-line5Markdown Sales by YearGrouped bar (5 series)6Weekly Sales by Store TypeHorizontal bar7Fuel Price by YearGrouped bar8Weekly Sales by Day of MonthBar9Weekly Sales by CPIFilled line/scatter10Department-Wise Weekly SalesBar (99 departments)

Every chart is a single, full-width visualization — no cluttered multi-panel subplots. KPI context (totals, percentage shares, best-performing segments) is folded directly into each chart title rather than tucked away in a separate pie chart or stat card.




🧩 Key Design Decisions


NULL_IF at the COPY INTO layer, not downstream in dbt — markdown columns use the literal string "NA" for missing values. Handling this at load time keeps every downstream model clean without repeated CASE WHEN logic.
SCD2 via dbt snapshot instead of hand-rolled MERGE — the store dimension changes over time (size, type); dbt snapshot gives us dbt_valid_from/dbt_valid_to for free instead of custom merge logic.
generate_schema_name macro — without it, dbt silently appends environment/user suffixes to schema names (e.g. SILVER_ted), which breaks downstream BI tool connections. This macro forces exact schema targeting in both dev and prod.
Python over a BI tool for final visuals — querying Snowflake directly via snowflake-connector-python and rendering with matplotlib/seaborn keeps the entire pipeline in one language and one repo, with chart code that's fully version-controlled.



📁 Repo Structure

walmart-de-project/
├── README.md
├── architecture/architecture_diagram.png
├── ingestion/upload_to_s3.py
├── snowflake/*.sql
├── dbt_project/
│   ├── models/staging/        (Silver)
│   ├── models/marts/          (Gold)
│   └── snapshots/             (SCD2)
└── visualizations/
    ├── walmart_visualizations.py
    └── walmart_charts/        (10 PNGs)