import logging
import os
import re
from pathlib import Path
from urllib.parse import quote_plus

import kagglehub
import pandas as pd

from dotenv import load_dotenv
from kagglehub import KaggleDatasetAdapter
from sqlalchemy import create_engine, text
from sqlalchemy.types import Text


# ==================================================
# 1. CONFIGURATION
# ==================================================

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

# Kaggle configuration
DATASET = "bakitacos/indonesia-e-commerce-sales-and-shipping-20232025"
FILE_PATH = "all_months_clean.csv"

# MySQL configuration
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

TABLE_NAME = "ecommerce_sales"

if not MYSQL_USER or not MYSQL_DATABASE:
    raise ValueError(
        "MYSQL_USER and MYSQL_DATABASE must be set in the .env file"
    )


# ==================================================
# 2. LOGGING CONFIGURATION
# ==================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "pipeline.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# ==================================================
# 3. EXTRACT DATA FROM KAGGLE
# ==================================================

def extract_data():
    """
    Load the latest version of the selected Kaggle dataset.
    """

    logger.info("Starting data extraction from Kaggle.")
    logger.info("Dataset: %s", DATASET)
    logger.info("File: %s", FILE_PATH)

    df = kagglehub.load_dataset(
        KaggleDatasetAdapter.PANDAS,
        DATASET,
        FILE_PATH,
        pandas_kwargs={
            "sep": ";",
            "on_bad_lines": "skip",
            "low_memory": False
        }
    )

    logger.info("Data extraction completed.")
    logger.info("Dataset shape: %s rows, %s columns",
                df.shape[0], df.shape[1])

    return df


# ==================================================
# 4. TRANSFORM DATA
# ==================================================

def transform_data(df):
    """
    Clean and prepare the DataFrame before loading it into MySQL.
    """

    logger.info("Starting data transformation.")

    df = df.copy()

    # Normalize column names
    df.columns = [
        re.sub(
            r"_+",
            "_",
            re.sub(
                r"[^a-zA-Z0-9]+",
                "_",
                str(column).strip().lower()
            )
        ).strip("_")
        for column in df.columns
    ]

    # Ensure column names are unique after normalization
    if df.columns.duplicated().any():
        duplicates = df.columns[df.columns.duplicated()].tolist()
        raise ValueError(
            f"Duplicate column names after normalization: {duplicates}"
        )

    # Remove completely empty rows
    initial_rows = len(df)
    df = df.dropna(how="all")

    logger.info(
        "Removed %s completely empty rows.",
        initial_rows - len(df)
    )

    # Remove exact duplicate rows
    initial_rows = len(df)
    df = df.drop_duplicates()

    logger.info(
        "Removed %s duplicate rows.",
        initial_rows - len(df)
    )

    # Replace infinity with missing values
    df = df.replace([float("inf"), float("-inf")], float("nan"))

    # Convert pandas missing values to Python None
    # This is useful when inserting nullable values into SQL.
    df = df.astype(object).where(pd.notna(df), None)

    logger.info("Data transformation completed.")
    logger.info("Final dataset shape: %s rows, %s columns",
                df.shape[0], df.shape[1])

    return df


# ==================================================
# 5. CREATE MYSQL CONNECTION
# ==================================================

def create_mysql_engine():
    """
    Create a SQLAlchemy engine for MySQL.
    """

    encoded_password = quote_plus(MYSQL_PASSWORD)

    connection_url = (
        f"mysql+pymysql://{MYSQL_USER}:{encoded_password}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
        "?charset=utf8mb4"
    )

    engine = create_engine(
        connection_url,
        pool_pre_ping=True
    )

    return engine


# ==================================================
# 6. LOAD DATA INTO MYSQL
# ==================================================

def to_sql(df, engine):
    """
    Load the DataFrame into a MySQL table.

    WARNING:
    if_exists='replace' drops and recreates the table
    if the table already exists.
    """

    if df.empty:
        logger.warning("DataFrame is empty. Nothing to load.")
        return

    logger.info("Starting data loading into MySQL.")
    logger.info("Target table: %s", TABLE_NAME)

    # Initial schema: store all columns as TEXT.
    # Define appropriate SQL data types for production use.
    column_types = {
        column: Text()
        for column in df.columns
    }

    df.to_sql(
        name=TABLE_NAME,
        con=engine,
        if_exists="replace",
        index=False,
        chunksize=1000,
        dtype=column_types,
        method="multi"
    )

    logger.info(
        "Successfully loaded %s rows into table '%s'.",
        len(df),
        TABLE_NAME
    )


# ==================================================
# 7. VERIFY LOADED DATA
# ==================================================

def verify_data(engine):
    """
    Check the number of rows stored in MySQL.
    """

    query = text(
        f"SELECT COUNT(*) FROM `{TABLE_NAME}`"
    )

    with engine.connect() as connection:
        total_rows = connection.execute(query).scalar_one()

    logger.info(
        "Verification completed. Total rows in MySQL: %s",
        total_rows
    )

    return total_rows


def main():

    engine = None

    try:
        logger.info("=" * 50)
        logger.info("ETL PIPELINE STARTED")
        logger.info("=" * 50)

        # Extract
        df = extract_data()

        # Transform
        df = transform_data(df)

        # Create MySQL connection
        engine = create_mysql_engine()

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        logger.info("MySQL connection successful.")

        # Load
        to_sql(df, engine)

        # Verify
        verify_data(engine)

        logger.info("ETL PIPELINE COMPLETED SUCCESSFULLY.")

    except Exception:
        logger.exception("ETL PIPELINE FAILED.")
        raise

    finally:
        if engine is not None:
            engine.dispose()
            logger.info("MySQL connection resources released.")


if __name__ == "__main__":
    main()