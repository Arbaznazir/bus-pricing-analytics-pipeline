"""
ETL Job for Bus Pricing Pipeline

PySpark-based ETL pipeline that:
1. Extracts raw bus schedule and occupancy data from JSON files
2. Transforms and cleans the data (removes anomalies, validates ranges)
3. Loads cleaned data into PostgreSQL database
4. Logs data quality issues for monitoring
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# PySpark imports
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, when, lit, isnan, isnull, regexp_replace,
    coalesce, round as spark_round, current_timestamp,
    from_json, explode, struct, to_timestamp
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    FloatType, TimestampType, BooleanType, ArrayType
)

# Database imports
import psycopg2
from sqlalchemy import create_engine
import pandas as pd

# Local imports
from .model import HeuristicPricingModel, validate_pricing_input

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BusDataETL:
    """
    ETL pipeline for bus scheduling and occupancy data
    """

    def __init__(self):
        # Environment configuration
        self.db_host = os.getenv("POSTGRES_HOST", "localhost")
        self.db_port = os.getenv("POSTGRES_PORT", "5432")
        self.db_name = os.getenv("POSTGRES_DB", "busdb")
        self.db_user = os.getenv("POSTGRES_USER", "bususer")
        self.db_password = os.getenv("POSTGRES_PASSWORD", "buspassword")

        # Data paths
        self.raw_data_path = os.getenv("RAW_DATA_PATH", "/app/data/raw")
        self.processed_data_path = os.getenv(
            "PROCESSED_DATA_PATH", "/app/data/processed")
        self.error_data_path = os.getenv("ERROR_DATA_PATH", "/app/data/error")

        # Data quality thresholds
        self.max_fare_threshold = float(
            os.getenv("MAX_FARE_THRESHOLD", "100000"))
        self.min_fare_threshold = float(os.getenv("MIN_FARE_THRESHOLD", "1"))

        # Create directories
        for path in [self.processed_data_path, self.error_data_path]:
            Path(path).mkdir(parents=True, exist_ok=True)

        # Database connection
        self.jdbc_url = f"jdbc:postgresql://{self.db_host}:{self.db_port}/{self.db_name}"
        self.db_properties = {
            "user": self.db_user,
            "password": self.db_password,
            "driver": "org.postgresql.Driver"
        }

        # Initialize Spark session
        self.spark = self._create_spark_session()

        # Initialize pricing model
        self.pricing_model = HeuristicPricingModel()

        # Data quality tracking
        self.quality_issues = []

    def _create_spark_session(self) -> SparkSession:
        """Create and configure Spark session"""
        try:
            spark = (SparkSession.builder
                     .appName("BusDataETL")
                     .config("spark.sql.adaptive.enabled", "true")
                     .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
                     # PostgreSQL JDBC driver
                     .config("spark.jars", "/opt/spark/jars/postgresql-42.6.0.jar")
                     .getOrCreate())

            # Set log level
            spark.sparkContext.setLogLevel("WARN")
            logger.info("Spark session created successfully")
            return spark

        except Exception as e:
            logger.error(f"Failed to create Spark session: {e}")
            raise

    def _get_database_connection(self):
        """Get direct database connection for metadata operations"""
        try:
            connection = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def load_metadata_to_db(self) -> Dict[str, Dict]:
        """Load routes and operators metadata to database and return mapping"""
        logger.info("Loading metadata to database...")

        metadata = {"routes": {}, "operators": {}}

        try:
            # Load routes metadata
            routes_file = Path(self.raw_data_path) / "routes_metadata.json"
            if routes_file.exists():
                with open(routes_file, 'r') as f:
                    routes_data = json.load(f)

                routes_df = pd.DataFrame(routes_data["routes"])

                # Use SQLAlchemy for easier DataFrame operations
                engine = create_engine(
                    f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}")

                # Insert routes (on conflict do nothing)
                routes_df.to_sql(
                    'routes', engine, if_exists='append', index=False, method='multi')

                # Create lookup mapping
                for route in routes_data["routes"]:
                    metadata["routes"][route["route_id"]] = route

                logger.info(
                    f"Loaded {len(routes_data['routes'])} routes to database")

            # Load operators metadata
            operators_file = Path(self.raw_data_path) / \
                "operators_metadata.json"
            if operators_file.exists():
                with open(operators_file, 'r') as f:
                    operators_data = json.load(f)

                operators_df = pd.DataFrame(operators_data["operators"])
                operators_df['is_active'] = True
                operators_df['created_at'] = datetime.utcnow()
                operators_df['updated_at'] = datetime.utcnow()

                operators_df.to_sql(
                    'operators', engine, if_exists='append', index=False, method='multi')

                # Create lookup mapping
                for operator in operators_data["operators"]:
                    metadata["operators"][operator["operator_id"]] = operator

                logger.info(
                    f"Loaded {len(operators_data['operators'])} operators to database")

            return metadata

        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            return metadata

    def read_schedule_data(self) -> Optional[DataFrame]:
        """Read and parse schedule data from JSON files"""
        try:
            schedule_files = list(
                Path(self.raw_data_path).glob("schedules_*.json"))

            if not schedule_files:
                logger.warning("No schedule files found")
                return None

            logger.info(f"Found {len(schedule_files)} schedule files")

            # Define schema for schedules
            schedule_schema = StructType([
                StructField("schedule_id", IntegerType(), True),
                StructField("route_id", IntegerType(), True),
                StructField("operator_id", IntegerType(), True),
                StructField("departure_time", StringType(), True),
                StructField("arrival_time", StringType(), True),
                StructField("date", StringType(), True),
                StructField("route_info", StructType([
                    StructField("origin", StringType(), True),
                    StructField("destination", StringType(), True),
                    StructField("distance_km", FloatType(), True)
                ]), True)
            ])

            all_schedules = []

            for file_path in schedule_files:
                try:
                    # Read JSON file
                    df = self.spark.read.option(
                        "multiline", "true").json(str(file_path))

                    # Extract schedules array and explode
                    schedules_df = df.select(
                        explode(col("schedules")).alias("schedule"))
                    schedules_df = schedules_df.select("schedule.*")

                    # Add source file for tracking
                    schedules_df = schedules_df.withColumn(
                        "source_file", lit(file_path.name))

                    all_schedules.append(schedules_df)

                except Exception as e:
                    logger.error(
                        f"Error reading schedule file {file_path}: {e}")
                    self._log_quality_issue(
                        "file_read_error", f"Failed to read {file_path}", str(e))

            if all_schedules:
                # Union all schedule DataFrames
                combined_schedules = all_schedules[0]
                for df in all_schedules[1:]:
                    combined_schedules = combined_schedules.union(df)

                logger.info(
                    f"Read {combined_schedules.count()} schedule records")
                return combined_schedules

            return None

        except Exception as e:
            logger.error(f"Failed to read schedule data: {e}")
            return None

    def read_occupancy_data(self) -> Optional[DataFrame]:
        """Read and parse occupancy data from JSON files"""
        try:
            occupancy_files = list(
                Path(self.raw_data_path).glob("occupancy_*.json"))

            if not occupancy_files:
                logger.warning("No occupancy files found")
                return None

            logger.info(f"Found {len(occupancy_files)} occupancy files")

            all_occupancy = []

            for file_path in occupancy_files:
                try:
                    # Read JSON file
                    df = self.spark.read.option(
                        "multiline", "true").json(str(file_path))

                    # Extract occupancy_records array and explode
                    occupancy_df = df.select(
                        explode(col("occupancy_records")).alias("occupancy"))
                    occupancy_df = occupancy_df.select("occupancy.*")

                    # Add source file for tracking
                    occupancy_df = occupancy_df.withColumn(
                        "source_file", lit(file_path.name))

                    all_occupancy.append(occupancy_df)

                except Exception as e:
                    logger.error(
                        f"Error reading occupancy file {file_path}: {e}")
                    self._log_quality_issue(
                        "file_read_error", f"Failed to read {file_path}", str(e))

            if all_occupancy:
                # Union all occupancy DataFrames
                combined_occupancy = all_occupancy[0]
                for df in all_occupancy[1:]:
                    combined_occupancy = combined_occupancy.union(df)

                logger.info(
                    f"Read {combined_occupancy.count()} occupancy records")
                return combined_occupancy

            return None

        except Exception as e:
            logger.error(f"Failed to read occupancy data: {e}")
            return None

    def clean_schedule_data(self, schedules_df: DataFrame) -> DataFrame:
        """Clean and validate schedule data"""
        logger.info("Cleaning schedule data...")

        initial_count = schedules_df.count()

        # Convert timestamp columns
        cleaned_df = schedules_df.withColumn(
            "departure_time",
            to_timestamp(col("departure_time"), "yyyy-MM-dd'T'HH:mm:ss")
        ).withColumn(
            "arrival_time",
            to_timestamp(col("arrival_time"), "yyyy-MM-dd'T'HH:mm:ss")
        ).withColumn(
            "date",
            to_timestamp(col("date"), "yyyy-MM-dd")
        )

        # Add metadata
        cleaned_df = cleaned_df.withColumn("is_active", lit(True))
        cleaned_df = cleaned_df.withColumn("created_at", current_timestamp())
        cleaned_df = cleaned_df.withColumn("updated_at", current_timestamp())

        # Filter out invalid records
        cleaned_df = cleaned_df.filter(
            col("schedule_id").isNotNull() &
            col("route_id").isNotNull() &
            col("operator_id").isNotNull() &
            col("departure_time").isNotNull() &
            col("arrival_time").isNotNull() &
            (col("arrival_time") > col("departure_time"))
        )

        final_count = cleaned_df.count()
        removed_count = initial_count - final_count

        if removed_count > 0:
            logger.warning(f"Removed {removed_count} invalid schedule records")
            self._log_quality_issue(
                "invalid_schedule", f"{removed_count} records had invalid data", "schedule_validation")

        logger.info(f"Schedule cleaning complete: {final_count} valid records")
        return cleaned_df

    def clean_occupancy_data(self, occupancy_df: DataFrame) -> DataFrame:
        """Clean and validate occupancy data with comprehensive quality checks"""
        logger.info("Cleaning occupancy data...")

        initial_count = occupancy_df.count()

        # Convert timestamp column
        cleaned_df = occupancy_df.withColumn(
            "timestamp",
            to_timestamp(col("timestamp"), "yyyy-MM-dd'T'HH:mm:ss")
        )

        # Data quality checks and cleaning

        # 1. Remove records with negative or zero fares
        before_fare_filter = cleaned_df.count()
        cleaned_df = cleaned_df.filter(
            (col("fare") > self.min_fare_threshold) &
            (col("fare") < self.max_fare_threshold)
        )
        after_fare_filter = cleaned_df.count()

        fare_removed = before_fare_filter - after_fare_filter
        if fare_removed > 0:
            logger.warning(
                f"Removed {fare_removed} records with invalid fares")
            self._log_quality_issue(
                "invalid_fare", f"{fare_removed} records with fares outside valid range", "fare_validation")

        # 2. Fix occupancy rates and validate seat counts
        cleaned_df = cleaned_df.withColumn(
            "occupancy_rate_calculated",
            when(col("total_seats") > 0, col("occupied_seats") /
                 col("total_seats")).otherwise(0)
        )

        # 3. Identify and handle impossible occupancy (occupied > total)
        impossible_occupancy = cleaned_df.filter(
            col("occupied_seats") > col("total_seats"))
        impossible_count = impossible_occupancy.count()

        if impossible_count > 0:
            logger.warning(
                f"Found {impossible_count} records with impossible occupancy")
            self._log_quality_issue(
                "impossible_occupancy", f"{impossible_count} records with occupied > total seats", "occupancy_validation")

            # Cap occupied seats at total seats
            cleaned_df = cleaned_df.withColumn(
                "occupied_seats",
                when(col("occupied_seats") > col("total_seats"), col(
                    "total_seats")).otherwise(col("occupied_seats"))
            )

        # 4. Recalculate occupancy rate after corrections
        cleaned_df = cleaned_df.withColumn(
            "occupancy_rate",
            when(col("total_seats") > 0, col("occupied_seats") /
                 col("total_seats")).otherwise(0)
        )

        # 5. Remove records with missing critical fields
        cleaned_df = cleaned_df.filter(
            col("schedule_id").isNotNull() &
            col("seat_type").isNotNull() &
            col("total_seats").isNotNull() &
            col("occupied_seats").isNotNull() &
            col("total_seats") > 0 &
            col("occupied_seats") >= 0 &
            col("timestamp").isNotNull()
        )

        # 6. Standardize seat types
        cleaned_df = cleaned_df.withColumn(
            "seat_type",
            when(col("seat_type").isin(
                ["regular", "premium", "sleeper"]), col("seat_type"))
            .otherwise("regular")  # Default unknown types to regular
        )

        # 7. Add metadata
        cleaned_df = cleaned_df.withColumn("created_at", current_timestamp())

        # 8. Round numerical values for consistency
        cleaned_df = cleaned_df.withColumn("fare", spark_round(col("fare"), 2))
        cleaned_df = cleaned_df.withColumn(
            "occupancy_rate", spark_round(col("occupancy_rate"), 3))

        final_count = cleaned_df.count()
        total_removed = initial_count - final_count

        logger.info(
            f"Occupancy cleaning complete: {final_count} valid records ({total_removed} removed)")

        return cleaned_df

    def _log_quality_issue(self, issue_type: str, description: str, details: str):
        """Log data quality issues for later reporting"""
        issue = {
            "issue_type": issue_type,
            "description": description,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.quality_issues.append(issue)

    def save_quality_issues_to_db(self):
        """Save data quality issues to database"""
        if not self.quality_issues:
            return

        try:
            # Convert to DataFrame and save
            issues_df = pd.DataFrame(self.quality_issues)
            issues_df['source_file'] = 'etl_job'
            issues_df['record_id'] = 'batch_' + \
                datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            issues_df['action_taken'] = 'logged'
            issues_df['original_value'] = None
            issues_df['corrected_value'] = None

            engine = create_engine(
                f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}")
            issues_df.to_sql('data_quality_log', engine,
                             if_exists='append', index=False)

            logger.info(
                f"Saved {len(self.quality_issues)} data quality issues to database")

        except Exception as e:
            logger.error(f"Failed to save quality issues: {e}")

    def write_to_database(self, df: DataFrame, table_name: str, mode: str = "append"):
        """Write DataFrame to PostgreSQL database"""
        try:
            logger.info(f"Writing {df.count()} records to {table_name}")

            df.write \
                .format("jdbc") \
                .option("url", self.jdbc_url) \
                .option("dbtable", table_name) \
                .option("user", self.db_user) \
                .option("password", self.db_password) \
                .option("driver", "org.postgresql.Driver") \
                .mode(mode) \
                .save()

            logger.info(f"Successfully wrote data to {table_name}")

        except Exception as e:
            logger.error(f"Failed to write to {table_name}: {e}")
            raise

    def move_processed_files(self):
        """Move processed files to processed directory"""
        try:
            raw_path = Path(self.raw_data_path)
            processed_path = Path(self.processed_data_path)

            # Move schedule files
            for file_path in raw_path.glob("schedules_*.json"):
                target_path = processed_path / file_path.name
                file_path.rename(target_path)
                logger.debug(f"Moved {file_path.name} to processed directory")

            # Move occupancy files
            for file_path in raw_path.glob("occupancy_*.json"):
                target_path = processed_path / file_path.name
                file_path.rename(target_path)
                logger.debug(f"Moved {file_path.name} to processed directory")

            logger.info("Successfully moved processed files")

        except Exception as e:
            logger.error(f"Failed to move processed files: {e}")

    def run_etl(self):
        """Main ETL pipeline execution"""
        logger.info("Starting ETL pipeline...")
        start_time = datetime.utcnow()

        try:
            # Step 1: Load metadata
            metadata = self.load_metadata_to_db()

            # Step 2: Read raw data
            schedules_df = self.read_schedule_data()
            occupancy_df = self.read_occupancy_data()

            if schedules_df is None and occupancy_df is None:
                logger.warning("No data files found to process")
                return

            # Step 3: Process schedules
            if schedules_df is not None:
                cleaned_schedules = self.clean_schedule_data(schedules_df)
                self.write_to_database(
                    cleaned_schedules.drop("source_file"), "schedules")

            # Step 4: Process occupancy data
            if occupancy_df is not None:
                cleaned_occupancy = self.clean_occupancy_data(occupancy_df)
                self.write_to_database(cleaned_occupancy.drop(
                    "source_file", "occupancy_rate_calculated"), "seat_occupancy")

            # Step 5: Save data quality issues
            self.save_quality_issues_to_db()

            # Step 6: Move processed files
            self.move_processed_files()

            # Step 7: Generate summary
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            logger.info(
                f"ETL pipeline completed successfully in {duration:.2f} seconds")
            logger.info(
                f"Data quality issues logged: {len(self.quality_issues)}")

        except Exception as e:
            logger.error(f"ETL pipeline failed: {e}")
            raise
        finally:
            # Stop Spark session
            if hasattr(self, 'spark'):
                self.spark.stop()


def main():
    """Entry point for ETL job"""
    logger.info("Starting Bus Data ETL Job")

    try:
        etl = BusDataETL()
        etl.run_etl()
        logger.info("ETL job completed successfully")

    except Exception as e:
        logger.error(f"ETL job failed: {e}")
        raise


if __name__ == "__main__":
    main()
