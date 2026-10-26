# Indonesia E-Commerce Sales: Kaggle to Looker

This repository documents a data workflow that takes Indonesia e-commerce sales data from Kaggle, cleans it with Python, stores it in MySQL, and makes it available for reporting in Looker. The repository contains the extraction and loading code plus sample SQL analysis queries. A Looker project or dashboard configuration is not included, so the final connection and visualization steps are completed in the Looker environment.

## Data workflow

```text
Kaggle dataset
      │
      ▼
Python ETL (main.py): extract → clean → load
      │
      ▼
MySQL database: ecommerce_sales table
      │
      ├── data_profiling.sql: sample analysis queries
      ▼
Looker: connect to the MySQL data → build an Explore/report/dashboard
```

### 1. Extract from Kaggle

`main.py` uses `kagglehub` to load `all_months_clean.csv` from the [`bakitacos/indonesia-e-commerce-sales-and-shipping-20232025`](https://www.kaggle.com/datasets/bakitacos/indonesia-e-commerce-sales-and-shipping-20232025) dataset. The file is read with a semicolon delimiter. Kaggle access must be configured for the account or environment running the script.

### 2. Transform with Python

Before loading, the pipeline uses pandas to:

- Normalize column names to lowercase letters, numbers, and underscores.
- Stop with an error if normalization creates duplicate column names.
- Remove fully empty rows and exact duplicate rows.
- Replace positive and negative infinity with missing values and convert missing values to SQL-compatible nulls.

This is the cleaning currently implemented in the code; it does not include broader business-rule validation or type parsing.

### 3. Load into MySQL

The pipeline connects to the MySQL database specified in `.env` and writes the data to `ecommerce_sales`. It verifies the result by counting rows and writes progress and errors to `logs/pipeline.log` as well as the console.

**Each run replaces the existing table.** The script uses `if_exists="replace"`, which drops and recreates `ecommerce_sales`. It also initially writes every column as `TEXT`. Before using the table for Looker measures, confirm that date and numeric fields have suitable database types or cast them in a SQL view. For example, sums over text columns may not behave as expected.

### 4. Connect Looker to MySQL

Once the table is loaded, configure a database connection in Looker using the host, port, database, and credentials for this MySQL instance.

To connect a SQL database on a local server to Looker, I'm using [this tutorial](https://anyquery.dev/connection-guide/looker-studio/)

For a more stable reporting layer, create database views with explicit date and numeric types and business-friendly field names, then expose those views to Looker. The sample `data_profiling.sql` queries can help inspect the loaded data before modeling it.

## Project files

| File                 | Description                                                                                   |
| -------------------- | --------------------------------------------------------------------------------------------- |
| `main.py`            | Extracts, transforms, and loads the data, then checks the loaded row count.                   |
| `data_profiling.sql` | Example SQL queries for inspecting orders, order statuses, product categories, and locations. |
| `preprocessing.sql`  | Reserved for SQL preprocessing queries; drop unused column; data cleaning.                    |
| `Screenhot.png`      | Dashboard screenshot                                                                          |

## Data source

The pipeline uses the [`bakitacos/indonesia-e-commerce-sales-and-shipping-20232025`](https://www.kaggle.com/datasets/bakitacos/indonesia-e-commerce-sales-and-shipping-20232025) Kaggle dataset and reads `all_months_clean.csv` with a semicolon (`;`) delimiter. `kagglehub` must be able to access Kaggle datasets in your environment. Follow Kaggle's authentication setup if prompted.

## Requirements

- Python 3.9 or newer
- A running MySQL server and a database to load into
- Kaggle access configured for `kagglehub`

Install the Python packages used by the pipeline:

```bash
pip install pandas kagglehub python-dotenv SQLAlchemy PyMySQL
```

## Configuration

Create a `.env` file in the repository root. The file is ignored by Git:

```dotenv
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=your_database
```

`MYSQL_USER` and `MYSQL_DATABASE` are required. `MYSQL_HOST`, `MYSQL_PORT`, and `MYSQL_PASSWORD` have defaults in the script (`localhost`, `3306`, and an empty password respectively). Ensure the configured MySQL user can create and replace tables in the selected database.

## Run the pipeline

```bash
python main.py
```

Running the command performs these steps:

1. Load the latest dataset version from Kaggle.
2. Normalize column names to lowercase letters, digits, and underscores.
3. Remove fully empty rows and exact duplicate rows, and replace infinite values with missing values.
4. Connect to MySQL and write the resulting data to `ecommerce_sales`.
5. Count the rows in the destination table and log the result.

Logs are written to `logs/pipeline.log` and printed to the console. The `logs/` directory is created automatically. The log file for this workflow was ignored by Git.

## Important loading behavior

The pipeline uses `if_exists="replace"` when writing the table. Each successful run drops and recreates `ecommerce_sales`, replacing its prior contents. It initially stores every column as MySQL `TEXT`; adjust the `column_types` mapping in `main.py` if you need typed numeric or date columns for downstream analysis.