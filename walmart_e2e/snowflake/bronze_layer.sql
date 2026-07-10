USE DATABASE MYDB_PROJECT

CREATE SCHEMA WALMART_BRONZE
CREATE SCHEMA WALMART_SILVER
CREATE SCHEMA WALMART_GOLD


--raw_stores table
CREATE OR REPLACE TABLE MYDB_PROJECT.WALMART_BRONZE.STORES_RAW(
    store varchar,
    type varchar,
    size varchar
)
;

--raw_fact table
CREATE OR REPLACE TABLE MYDB_PROJECT.WALMART_BRONZE.FACT_RAW(
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
CREATE OR REPLACE TABLE MYDB_PROJECT.WALMART_BRONZE.DEPARTMENT_RAW(
    store varchar,
    dept varchar,
    date varchar,
    weekly_sales varchar,
    isholiday varchar
)
;


--------------------------------------------------------------------------------------------

COPY INTO MYDB_PROJECT.WALMART_BRONZE.STORES_RAW
    FROM @walmart_stage/stores/
    FILE_FORMAT = walmart_csv_fmt
    ON_ERROR = ABORT_STATEMENT
;

COPY INTO MYDB_PROJECT.WALMART_BRONZE.FACT_RAW
    FROM @walmart_stage/fact/
    FILE_FORMAT = walmart_csv_fmt
    ON_ERROR = ABORT_STATEMENT
;
COPY INTO MYDB_PROJECT.WALMART_BRONZE.DEPARTMENT_RAW
    FROM @walmart_stage/department/
    FILE_FORMAT = walmart_csv_fmt
    ON_ERROR = ABORT_STATEMENT
;