USE DATABASE MYDB_PROJECT

CREATE SCHEMA RETAIL_BRONZE
CREATE SCHEMA RETAIL_SILVER
CREATE SCHEMA RETAIL_GOLD


--raw_stores table
CREATE OR REPLACE TABLE MYDB_PROJECT.RETAIL_BRONZE.STORES_RAW(
    store varchar,
    type varchar,
    size varchar
)
;

--raw_fact table
CREATE OR REPLACE TABLE MYDB_PROJECT.RETAIL_BRONZE.FACT_RAW(
    store varchar,
    date varchar,
    temperature varchar,
    fuel_price varchar, 
    markdown1 varchar,
    markdown2 varchar,
    markdown3 varchar,
    markdown4 varchar,
    markdown5 varchar,
    cpi varchar,
    unemployement varchar,
    isholiday varchar
)
;

--raw_department table
CREATE OR REPLACE TABLE MYDB_PROJECT.RETAIL_BRONZE.DEPARTMENT_RAW(
    store varchar,
    dept varchar,
    date varchar,
    weekly_sales varchar,
    isholiday varchar
)
;


--------------------------------------------------------------------------------------------

COPY INTO MYDB_PROJECT.RETAIL_BRONZE.STORES_RAW
    FROM @RETAIL_stage/stores/
    FILE_FORMAT = RETAIL_csv_fmt
    ON_ERROR = ABORT_STATEMENT
;

COPY INTO MYDB_PROJECT.RETAIL_BRONZE.FACT_RAW
    FROM @RETAIL_stage/fact/
    FILE_FORMAT = RETAIL_csv_fmt
    ON_ERROR = ABORT_STATEMENT
;
COPY INTO MYDB_PROJECT.RETAIL_BRONZE.DEPARTMENT_RAW
    FROM @RETAIL_stage/department/
    FILE_FORMAT = RETAIL_csv_fmt
    ON_ERROR = ABORT_STATEMENT
;
