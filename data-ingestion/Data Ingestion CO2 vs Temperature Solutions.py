# Databricks notebook source
# MAGIC %md
# MAGIC # Data Ingestion: CO2 vs. Temperature
# MAGIC In this exercise, we'll be studying the correlation between CO2 Emissions and Temperatures around the world. 
# MAGIC 
# MAGIC Some of the questions we want to answer:
# MAGIC * Which countries are worse-hit (higher temperature anomalies)?
# MAGIC * Which countries are the biggest emitters? 
# MAGIC * What are some attempts of ranking “biggest polluters” in a sensible way?

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Sources
# MAGIC In order to answer some of our questions, we start with open-source data from <a href="https://github.com/owid/owid-datasets/tree/0f47d280d298694c50b82db98daa94cd6e867d2e/datasets/CO2%20emissions%20(Aggregate%20dataset%20(2020))">Open World in Data (OWID)</a> and [Kaggle](https://www.kaggle.com/berkeleyearth/climate-change-earth-surface-temperature-data).
# MAGIC 
# MAGIC The specific datasets we'd use to answer our questions would be the following:
# MAGIC * <a href="https://github.com/owid/owid-datasets/blob/0f47d280d298694c50b82db98daa94cd6e867d2e/datasets/CO2%20emissions%20(Aggregate%20dataset%20(2020))/CO2%20emissions%20(Aggregate%20dataset%20(2020)).csv">CO2 Emissions (2020).csv from OWID</a>
# MAGIC * [GlobalLandTemperaturesByCountry (Kaggle)](https://www.kaggle.com/berkeleyearth/climate-change-earth-surface-temperature-data?select=GlobalLandTemperaturesByCountry.csv)
# MAGIC * [GlobalTemperatures.csv (Kaggle)](https://www.kaggle.com/berkeleyearth/climate-change-earth-surface-temperature-data?select=GlobalTemperatures.csv)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Sources (Modified!)
# MAGIC Since the point of this exercise is to learn how to work with data and the datasets from OWID and Kaggle are both too clean and curated, a set of dirtied data is provided.
# MAGIC 
# MAGIC They can be found at:
# MAGIC * https://raw.githubusercontent.com/data-derp/exercise-co2-vs-temperature/master/data-ingestion/input-data/EmissionsByCountry.csv
# MAGIC * https://raw.githubusercontent.com/data-derp/exercise-co2-vs-temperature/master/data-ingestion/input-data/GlobalTemperatures.csv
# MAGIC * https://raw.githubusercontent.com/data-derp/exercise-co2-vs-temperature/master/data-ingestion/input-data/TemperaturesByCountry.csv

# COMMAND ----------

# MAGIC %md
# MAGIC ## Milestones of Exercises
# MAGIC 1. Load data into DataFrames
# MAGIC 2. Clean up invalid column names
# MAGIC 3. Fix columns
# MAGIC 4. Write to parquet

# COMMAND ----------

# MAGIC %md
# MAGIC ## EXERCISE: Download data from an online repository into a Spark DataFrame  
# MAGIC - The data for our mini-project is accessible at GitHub via the URLs in the cell above.
# MAGIC - However, Spark (at the time of writing) does not support reading data directly from arbitrary http(s) addresses.
# MAGIC - In practice, **you would not want to do this with big data anyways**.  
# MAGIC   It's much better to load big data into a data lake (e.g. S3, Azure Data Lake Storage Gen2, or Azure Blob Storage).  
# MAGIC   You can then use the connectors that come with your cloud offering (e.g. Databricks, AWS Glue, or AWS EMR) to read from these data lakes.  
# MAGIC   [See Example](https://docs.databricks.com/data/data-sources/azure/adls-gen2/azure-datalake-gen2-get-started.html#get-started-with-azure-data-lake-storage-gen2)
# MAGIC   
# MAGIC - For the sake of simplicity in this exercise, let's not worry about transferring these datasets to S3 yet
# MAGIC 
# MAGIC **Objectives**
# MAGIC - Let's simply download the data first, then read the CSV files with Spark
# MAGIC - Learn how to set some important parameters for the Spark CSV Reader
# MAGIC - Run the following cells and inspect the resulting DataFrames

# COMMAND ----------

# MAGIC %pip install wget

# COMMAND ----------

# MAGIC %sh
# MAGIC # clear out all CSV files in local filesystem
# MAGIC rm -rf *Emissions*.csv
# MAGIC rm -rf *Temperatures*.csv

# COMMAND ----------

# Set URLS of modified datasets
CO2_URL = "https://raw.githubusercontent.com/data-derp/exercise-co2-vs-temperature/master/data-ingestion/input-data/EmissionsByCountry.csv"
GLOBAL_TEMPERATURES_URL = "https://raw.githubusercontent.com/data-derp/exercise-co2-vs-temperature/master/data-ingestion/input-data/GlobalTemperatures.csv"
TEMPERATURES_BY_COUNTRY_URL = "https://raw.githubusercontent.com/data-derp/exercise-co2-vs-temperature/master/data-ingestion/input-data/TemperaturesByCountry.csv"

# COMMAND ----------

# Download files to the local filesystem
import os
import wget

URLS = [CO2_URL, GLOBAL_TEMPERATURES_URL, TEMPERATURES_BY_COUNTRY_URL]
filenames = []

for url in URLS:
  saved_filename = wget.download(url, url.split("/")[-1])
  filenames.append(saved_filename)

LOCAL_DIR = os.getcwd()
print("LOCAL_DIR:", LOCAL_DIR)
print("filenames:", filenames)

# COMMAND ----------

# Set up a DBFS directory to keep a copy of our data in a distributed filesystem (rather than local/single-node)
# Copy over the files from the local filesystem to our new DBFS directory (mini-project)
# (so that Spark can read in a performant manner from dbfs:/)

MINI_PROJECT_DIR = "dbfs:/FileStore/mini-project/"
dbutils.fs.rm(MINI_PROJECT_DIR, True) # delete directory, start fresh
dbutils.fs.mkdirs(MINI_PROJECT_DIR)

for filename in filenames: # copy from local file system into a distributed file system such as DBFS
  dbutils.fs.cp(f"file:{LOCAL_DIR}/{filename}", f"{MINI_PROJECT_DIR}{filename}")
  
DBFS_FILEPATHS = [x.path for x in dbutils.fs.ls(MINI_PROJECT_DIR)]
print(DBFS_FILEPATHS)
CO2_PATH, GLOBAL_TEMPERATURES_PATH, TEMPERATURES_BY_COUNTRY_PATH = DBFS_FILEPATHS

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC #### [Optional] Confused or curious about DBFS?
# MAGIC - Don't worry! it's a bit confusing for everyone initially
# MAGIC - [See this summary table and diagram](https://docs.databricks.com/data/databricks-file-system.html#summary-table-and-diagram)
# MAGIC - [Having trouble with `/dbfs/` on Databricks Community Edition?](https://stackoverflow.com/questions/63608357/cant-access-dbfs-filestore-using-shell-commands-in-databricks-runtime-version#:~:text=The%20/dbfs%20mount%20doesn%27t%20work%20on%20Community%20Edition%20with%20DBR%20%3E%3D%207.x%20%2D%20it%27s%20a%20known%20limitation.)

# COMMAND ----------

# Load EmissionsByCountry.csv

co2_df = spark.read.csv(CO2_PATH, header=True, inferSchema=True)
display(co2_df)

# COMMAND ----------

# Load GlobalTemperatures.csv
global_temperatures_df = spark.read.csv(GLOBAL_TEMPERATURES_PATH, header=True, inferSchema=True)
display(global_temperatures_df)

# COMMAND ----------

# Load TemperaturesByCountry.csv
temperatures_by_country_df = spark.read.csv(TEMPERATURES_BY_COUNTRY_PATH, header=True, inferSchema=True)
display(temperatures_by_country_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Summary and Hints
# MAGIC Notice anything interesting about the quality of data?  
# MAGIC **Note:** If not using Databricks, you can still view of the DataFrame by using `some_dataframe.show()`

# COMMAND ----------

temperatures_by_country_df.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## EXERCISE: Clean Invalid Column Names
# MAGIC The format that we'll want to convert to will be [Apache Parquet](https://parquet.apache.org/) but some of the columns in our DataFrames contain invalid characters (`[" ", ",", ";", "\n", "\t", "=", "-", "{", "}", "(", ")"]`). Implement a function that modifies invalid characters by replacing any of the following `[" ", ",", ";", "\n", "\t", "=", "-"]` with an underscore, else an empty string `""`. This exercise is about generating the logic that would do the replacement, but the actual replacement will occur in the next exercise. Don't forget to run the tests!

# COMMAND ----------

def replace_invalid_chars(column_name: str) -> str:
        """Replace prohibited characters in column names to be compatible with Apache Parquet"""
        INVALID_CHARS = [" ", ",", ";", "\n", "\t", "=", "-", "{", "}", "(", ")"]
        UNDERSCORE_CANDIDATES = [" ", ",", ";", "\n", "\t", "=", "-"] # let's replace these with underscores

        column_name = NotImplemented # TODO: Exercise (modify however necessary, no need to be a one-liner)
        if column_name is NotImplemented:
            raise NotImplementedError("DO YOUR HOMEWORK OR NO CHEESECAKE")
        return column_name

# COMMAND ----------

####### SOLUTION ########
def replace_invalid_chars(column_name: str) -> str:
        """Replace prohibited characters in column names to be compatiable with Apache Parquet"""
        INVALID_CHARS = [" ", ",", ";", "\n", "\t", "=", "-", "{", "}", "(", ")"]
        UNDERSCORE_CANDIDATES = [" ", ",", ";", "\n", "\t", "=", "-"] # let's replace these with underscores
        for char in INVALID_CHARS:
            replacement = "_" if char in UNDERSCORE_CANDIDATES else ""
            column_name = column_name.replace(char, replacement)
        return column_name

# COMMAND ----------

import pandas as pd

def test_replace_invalid_chars():
    # BEWARE: dictionaries do not necessarily enforce order.
    # To check column names, always use sorted()
    INVALID_CHARS = [" ", ",", ";", "\n", "\t", "=", "-", "{", "}", "(", ")"]
    df = pd.DataFrame(
        {
            'My Awesome Column': pd.Series(["Germany", "New Zealand", "Australia", "UK"]),
            '(Another) Awesome Column': pd.Series(["Germany", "New Zealand", "Australia", "UK"]),
        }
    )
    df.columns = [replace_invalid_chars(x) for x in df.columns]

    all_columns_valid = True
    for column in df.columns:
        if not all_columns_valid:
            break
        for char in INVALID_CHARS:
            if char in column:
                all_columns_valid = False
                break
    assert all_columns_valid
    assert sorted(df.columns) == sorted(["My_Awesome_Column", "Another_Awesome_Column"])
    print("All tests passed :)")
        
test_replace_invalid_chars()

# COMMAND ----------

# MAGIC %md
# MAGIC ## EXERCISE: Fix Columns
# MAGIC Now that we have the logic that fixes invalid column names, let's actually apply that to our columns. Don't forget to run the tests!

# COMMAND ----------

from pyspark.sql import DataFrame
import pyspark.sql.functions as F

def fix_columns(df: DataFrame) -> DataFrame:
        """Clean up a Spark DataFrame's column names"""
        # HINT: you don't need to do use .withColumnRenamed a dozen times - one-liner solution possible ;)
        fixed_df = NotImplemented # TODO: Exercise (modify however necessary, no need to be a one-liner)
        if fixed_df is NotImplemented:
            raise NotImplementedError("DO YOUR HOMEWORK OR NO BREZE")
        return fixed_df

# COMMAND ----------

######## SOLUTION ###########
from pyspark.sql import DataFrame
import pyspark.sql.functions as F

def fix_columns(df: DataFrame) -> DataFrame:
    """Clean up a Spark DataFrame's column names"""
    # HINT: you don't need to do use .withColumnRenamed a dozen times - one-liner solution possible ;)
    fixed_df = df.select([F.col(x).alias(replace_invalid_chars(x)) for x in df.columns])
    return fixed_df

# COMMAND ----------

def test_fix_columns():
  # BEWARE: dictionaries do not necessarily enforce order.
  # To check column names, always use sorted()
  pandas_df = pd.DataFrame(
      {
          'My Awesome Column': pd.Series(["Germany", "New Zealand", "Australia", "UK"]),
          '(Another) Awesome Column': pd.Series(["Germany", "New Zealand", "Australia", "UK"]),
      }
  )
  spark_df = spark.createDataFrame(pandas_df)
  fixed_df = fix_columns(spark_df)
  assert sorted(fixed_df.columns) == sorted(["My_Awesome_Column", "Another_Awesome_Column"])
  print("All tests passed :)")
  
test_fix_columns()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Let's put it together
# MAGIC For fun, let's have a look at how this new function changes our current DataFrames...

# COMMAND ----------

display(fix_columns(co2_df))
# display(fix_columns(global_temperatures_df))
# display(fix_columns(temperatures_by_country_df))

# COMMAND ----------

# MAGIC %md
# MAGIC ## EXERCISE: Write to Parquet
# MAGIC Now that we have a function that updates invalid characters in our columns in our DataFrames, the last step is to write our DataFrames out to the Parquet format. For this exercise, we'll write to a DBFS directory called (`dbfs:/FileStore/mini-project/data-ingestion/`) so that we can use the output for another exercise in the future.
# MAGIC 
# MAGIC **Requirements**
# MAGIC - Each output dataset must be in Parquet format
# MAGIC - For this task, we want only 1 Parquet partition per dataset
# MAGIC - Any old/existing data in each output path should simply be overwritten
# MAGIC 
# MAGIC Let's first do this together for `co2_df`

# COMMAND ----------

# Write co2_df to parquet

EMISSIONS_OUTPUT_FILENAME = "EmissionsByCountry.parquet"
EMISSIONS_OUTPUT_PATH = MINI_PROJECT_DIR + "data-ingestion/" + EMISSIONS_OUTPUT_FILENAME + "/"
dbutils.fs.rm(EMISSIONS_OUTPUT_PATH, True)
print(EMISSIONS_OUTPUT_PATH)

# How do we ensure the output dataset will have only 1 partition?
# Check out: https://spark.apache.org/docs/latest/api/python/reference/api/pyspark.sql.DataFrame.coalesce.html
# Not to be confused with pyspark.sql.functions.coalesce! (you'll see this later in the mini-project)

co2_fixed = fix_columns(co2_df).coalesce(1) 
co2_write_resp = co2_fixed.write.format("parquet").mode("overwrite").save(EMISSIONS_OUTPUT_PATH)
assert (co2_write_resp is None)

# COMMAND ----------

# Confirm files have been written
# there should be only ONE .snappy.parquet file (i.e. ONE partition)
dbutils.fs.ls(EMISSIONS_OUTPUT_PATH)

# COMMAND ----------

# Confirm written parquet file can be read again
read_co2_df = spark.read.parquet(EMISSIONS_OUTPUT_PATH)
display(read_co2_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## On your own
# MAGIC Similar to how we wrote `co2_df` to a parquet file, please do the same for `global_temperatures_df` and `temperatures_by_country_df`. Don't forget to `coalesce(1)` from the above example. 
# MAGIC 
# MAGIC | DataFrame | Output Path |
# MAGIC | --- | --- |
# MAGIC | global_temperatures_df | dbfs:/FileStore/mini-project/data-ingestion/GlobalTemperatures.parquet/ |
# MAGIC | temperatures_by_country_df | dbfs:/FileStore/mini-project/data-ingestion/TemperaturesByCountry.parquet/ |

# COMMAND ----------

GLOBAL_TEMPS_OUTPUT_FILENAME = "GlobalTemperatures.parquet"
GLOBAL_TEMPS_OUTPUT_PATH = MINI_PROJECT_DIR + "data-ingestion/" + GLOBAL_TEMPS_OUTPUT_FILENAME + "/"
dbutils.fs.rm(GLOBAL_TEMPS_OUTPUT_PATH, True)

global_temperatures_fixed = NotImplemented
global_temperatures_write_resp = NotImplemented

COUNTRY_TEMPS_OUTPUT_FILENAME = "TemperaturesByCountry.parquet"
COUNTRY_TEMPS_OUTPUT_PATH = MINI_PROJECT_DIR + "data-ingestion/" + COUNTRY_TEMPS_OUTPUT_FILENAME + "/"
dbutils.fs.rm(COUNTRY_TEMPS_OUTPUT_PATH, True)

temperatures_by_country_fixed = NotImplemented
temperatures_by_country_write_resp = NotImplemented

if any(x is NotImplemented for x in [global_temperatures_write_resp, temperatures_by_country_write_resp]):
  raise NotImplementedError("DO YOUR HOMEWORK OR NO LEBKUCHEN")

# COMMAND ----------

######### SOLUTION ##########
GLOBAL_TEMPS_OUTPUT_FILENAME = "GlobalTemperatures.parquet"
GLOBAL_TEMPS_OUTPUT_PATH = MINI_PROJECT_DIR + "data-ingestion/" + GLOBAL_TEMPS_OUTPUT_FILENAME + "/"
dbutils.fs.rm(GLOBAL_TEMPS_OUTPUT_PATH, True)

global_temperatures_fixed = fix_columns(global_temperatures_df).coalesce(1)
global_temperatures_write_resp = (
  global_temperatures_fixed
    .write.format("parquet").mode("overwrite")
    .save(GLOBAL_TEMPS_OUTPUT_PATH)
)

COUNTRY_TEMPS_OUTPUT_FILENAME = "TemperaturesByCountry.parquet"
COUNTRY_TEMPS_OUTPUT_PATH = MINI_PROJECT_DIR + "data-ingestion/" + COUNTRY_TEMPS_OUTPUT_FILENAME + "/"
dbutils.fs.rm(COUNTRY_TEMPS_OUTPUT_PATH, True)

temperatures_by_country_fixed = fix_columns(temperatures_by_country_df).coalesce(1)
temperatures_by_country_write_resp = (
  temperatures_by_country_fixed
    .write.format("parquet").mode("overwrite")
    .save(COUNTRY_TEMPS_OUTPUT_PATH)
)

if any(x is NotImplemented for x in [global_temperatures_write_resp, temperatures_by_country_write_resp]):
  raise NotImplementedError("DO YOUR HOMEWORK OR NO LEBKUCHEN")

# COMMAND ----------

INGESTION_OUTPUTS_DIR = MINI_PROJECT_DIR + "data-ingestion" + "/"

path = dbutils.fs.ls(INGESTION_OUTPUTS_DIR)
files_df = spark.createDataFrame(path)
assert files_df.filter(F.col('name') == "EmissionsByCountry.parquet/").count() == 1, "EmissionsByCountry.parquet/ is missing"
assert files_df.filter(F.col('name') == "GlobalTemperatures.parquet/").count() == 1, "GlobalTemperatures.parquet/ is missing"
assert files_df.filter(F.col('name') == "TemperaturesByCountry.parquet/").count() == 1, "TemperaturesByCountry.parquet/ is missing"
print("All tests passed :)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC In this exercise, you will have learned how to ingest a CSV, apply a transformation function that changes the column names, and write the resulting DataFrames to a parquet file. 
# MAGIC 
# MAGIC You might have noticed that `temperatures_by_country_df` has some interesting facets in the data. We'll address that in the next exercise...

# COMMAND ----------

display(temperatures_by_country_df)

# COMMAND ----------


