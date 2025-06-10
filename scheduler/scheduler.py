"""
Scheduler Service for Bus Pricing Pipeline

Manages the automated execution of ETL jobs and other scheduled tasks.
Uses APScheduler for job scheduling and monitoring.
"""

import os
import time
import logging
import subprocess
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import requests
import psycopg2
from sqlalchemy import create_engine, text
import pandas as pd

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BusDataScheduler:
    """
    Scheduler for automating bus data pipeline tasks

    Responsibilities:
    - Trigger ETL jobs at configured intervals
    - Monitor job execution and health
    - Generate data freshness reports
    - Cleanup old processed files
    - System health monitoring
    """

    def __init__(self):
        # Configuration from environment
        self.etl_interval_seconds = int(
            # 5 minutes default
            os.getenv("ETL_SCHEDULE_INTERVAL_SECONDS", "300"))
        self.cleanup_interval_hours = int(
            os.getenv("CLEANUP_INTERVAL_HOURS", "24"))  # Daily cleanup
        self.health_check_interval_minutes = int(
            os.getenv("HEALTH_CHECK_INTERVAL_MINUTES", "5"))

        # Database configuration
        self.db_host = os.getenv("POSTGRES_HOST", "localhost")
        self.db_port = os.getenv("POSTGRES_PORT", "5432")
        self.db_name = os.getenv("POSTGRES_DB", "busdb")
        self.db_user = os.getenv("POSTGRES_USER", "bususer")
        self.db_password = os.getenv("POSTGRES_PASSWORD", "buspassword")

        # API configuration
        self.api_host = os.getenv("API_HOST", "api")
        self.api_port = os.getenv("API_PORT", "8000")
        self.api_base_url = f"http://{self.api_host}:{self.api_port}"

        # Data paths
        self.raw_data_path = os.getenv("RAW_DATA_PATH", "/app/data/raw")
        self.processed_data_path = os.getenv(
            "PROCESSED_DATA_PATH", "/app/data/processed")

        # Initialize scheduler
        self.scheduler = BlockingScheduler()
        self.scheduler.add_listener(
            self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

        # Job execution tracking
        self.job_history = []
        self.system_status = {
            "last_etl_run": None,
            "last_etl_success": None,
            "etl_consecutive_failures": 0,
            "api_health": "unknown",
            "database_health": "unknown"
        }

    def _job_listener(self, event):
        """Listen to job execution events for monitoring"""
        job_id = event.job_id

        if event.exception:
            logger.error(f"Job {job_id} failed: {event.exception}")
            if job_id == "etl_job":
                self.system_status["etl_consecutive_failures"] += 1
        else:
            logger.info(f"Job {job_id} executed successfully")
            if job_id == "etl_job":
                self.system_status["last_etl_success"] = datetime.utcnow()
                self.system_status["etl_consecutive_failures"] = 0

        # Record job history
        self.job_history.append({
            "job_id": job_id,
            "execution_time": datetime.utcnow(),
            "success": event.exception is None,
            "error_message": str(event.exception) if event.exception else None
        })

        # Keep only last 100 job history entries
        self.job_history = self.job_history[-100:]

    def check_database_health(self) -> bool:
        """Check database connectivity and health"""
        try:
            connection = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                connect_timeout=10
            )

            # Test with a simple query
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            connection.close()

            self.system_status["database_health"] = "healthy"
            return True

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            self.system_status["database_health"] = f"unhealthy: {str(e)}"
            return False

    def check_api_health(self) -> bool:
        """Check API service health"""
        try:
            response = requests.get(
                f"{self.api_base_url}/health",
                timeout=10
            )

            if response.status_code == 200:
                self.system_status["api_health"] = "healthy"
                return True
            else:
                self.system_status["api_health"] = f"unhealthy: HTTP {response.status_code}"
                return False

        except Exception as e:
            logger.error(f"API health check failed: {e}")
            self.system_status["api_health"] = f"unhealthy: {str(e)}"
            return False

    def check_for_new_data(self) -> bool:
        """Check if there are new data files to process"""
        try:
            import glob

            # Check for new schedule and occupancy files
            schedule_files = glob.glob(
                f"{self.raw_data_path}/schedules_*.json")
            occupancy_files = glob.glob(
                f"{self.raw_data_path}/occupancy_*.json")

            new_files_count = len(schedule_files) + len(occupancy_files)

            if new_files_count > 0:
                logger.info(
                    f"Found {new_files_count} new data files to process")
                return True
            else:
                logger.debug("No new data files found")
                return False

        except Exception as e:
            logger.error(f"Error checking for new data: {e}")
            return False

    def run_etl_job(self):
        """Execute the ETL job"""
        logger.info("Starting scheduled ETL job...")
        self.system_status["last_etl_run"] = datetime.utcnow()

        try:
            # Check prerequisites
            if not self.check_database_health():
                raise Exception("Database health check failed - skipping ETL")

            # Check for new data (optional - run ETL even if no new data for maintenance)
            has_new_data = self.check_for_new_data()
            if not has_new_data:
                logger.info(
                    "No new data found, but running ETL for maintenance")

            # Execute ETL job using subprocess (Docker container execution)
            # In production, this would be replaced with proper container orchestration
            result = subprocess.run(
                ["python3", "/app/etl/etl_job.py"],
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )

            if result.returncode == 0:
                logger.info("ETL job completed successfully")
                logger.debug(f"ETL output: {result.stdout}")
            else:
                logger.error(
                    f"ETL job failed with return code {result.returncode}")
                logger.error(f"ETL error: {result.stderr}")
                raise Exception(f"ETL job failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            logger.error("ETL job timed out after 30 minutes")
            raise Exception("ETL job timeout")
        except Exception as e:
            logger.error(f"ETL job execution failed: {e}")
            raise

    def run_data_simulation(self):
        """Trigger data simulation to generate new test data"""
        logger.info("Running data simulation...")

        try:
            # Execute data simulator
            result = subprocess.run(
                ["python3", "/app/data_simulator/simulator.py"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                logger.info("Data simulation completed successfully")
                logger.debug(f"Simulator output: {result.stdout}")
            else:
                logger.error(f"Data simulation failed: {result.stderr}")
                raise Exception(f"Data simulation failed: {result.stderr}")

        except Exception as e:
            logger.error(f"Data simulation failed: {e}")
            raise

    def cleanup_old_files(self):
        """Clean up old processed files and logs"""
        logger.info("Running cleanup task...")

        try:
            import glob
            import os
            from pathlib import Path

            # Define retention period (default: 7 days)
            retention_days = int(os.getenv("FILE_RETENTION_DAYS", "7"))
            cutoff_time = datetime.now() - timedelta(days=retention_days)

            cleaned_count = 0

            # Clean processed data files
            processed_files = glob.glob(f"{self.processed_data_path}/*")
            for file_path in processed_files:
                file_stat = os.stat(file_path)
                file_time = datetime.fromtimestamp(file_stat.st_mtime)

                if file_time < cutoff_time:
                    os.remove(file_path)
                    cleaned_count += 1
                    logger.debug(f"Removed old file: {file_path}")

            logger.info(
                f"Cleanup completed: removed {cleaned_count} old files")

        except Exception as e:
            logger.error(f"Cleanup task failed: {e}")
            raise

    def generate_data_freshness_report(self):
        """Generate and log data freshness report"""
        logger.info("Generating data freshness report...")

        try:
            engine = create_engine(
                f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}")

            # Query for data freshness metrics
            query = """
            SELECT 
                COUNT(*) as total_records,
                MAX(created_at) as latest_record,
                MIN(created_at) as oldest_record,
                COUNT(DISTINCT DATE(created_at)) as data_days
            FROM seat_occupancy 
            WHERE created_at >= NOW() - INTERVAL '7 days'
            """

            with engine.connect() as conn:
                result = conn.execute(text(query))
                row = result.fetchone()

                if row:
                    report = {
                        "total_records_last_7_days": row[0],
                        "latest_record_time": row[1],
                        "oldest_record_time": row[2],
                        "days_with_data": row[3],
                        "report_generated_at": datetime.utcnow()
                    }

                    logger.info(f"Data freshness report: {report}")
                else:
                    logger.warning("No data found for freshness report")

        except Exception as e:
            logger.error(f"Failed to generate data freshness report: {e}")

    def health_check_job(self):
        """Comprehensive system health check"""
        logger.debug("Running system health check...")

        try:
            # Check database health
            db_healthy = self.check_database_health()

            # Check API health
            api_healthy = self.check_api_health()

            # Check ETL job health (based on recent execution)
            etl_healthy = (
                self.system_status["etl_consecutive_failures"] < 3 and
                (self.system_status["last_etl_success"] is None or
                 # Within last hour
                 (datetime.utcnow() - self.system_status["last_etl_success"]).total_seconds() < 3600)
            )

            # Overall system health
            overall_health = db_healthy and api_healthy and etl_healthy

            if not overall_health:
                logger.warning(
                    f"System health issues detected: DB={db_healthy}, API={api_healthy}, ETL={etl_healthy}")
            else:
                logger.debug("System health check passed")

            # Store health status (could be extended to send alerts)
            self.system_status["last_health_check"] = datetime.utcnow()

        except Exception as e:
            logger.error(f"Health check failed: {e}")

    def setup_jobs(self):
        """Setup all scheduled jobs"""
        logger.info("Setting up scheduled jobs...")

        # ETL job - runs at configured interval
        self.scheduler.add_job(
            func=self.run_etl_job,
            trigger=IntervalTrigger(seconds=self.etl_interval_seconds),
            id="etl_job",
            name="ETL Data Processing",
            max_instances=1,  # Prevent overlapping executions
            coalesce=True,    # If job is missed, run only the latest
            misfire_grace_time=60
        )

        # Data simulation - runs every 30 minutes to generate fresh test data
        self.scheduler.add_job(
            func=self.run_data_simulation,
            trigger=IntervalTrigger(minutes=30),
            id="data_simulation",
            name="Data Simulation",
            max_instances=1
        )

        # Cleanup job - runs daily at 2 AM
        self.scheduler.add_job(
            func=self.cleanup_old_files,
            trigger=CronTrigger(hour=2, minute=0),
            id="cleanup_job",
            name="File Cleanup",
            max_instances=1
        )

        # Data freshness report - runs every 4 hours
        self.scheduler.add_job(
            func=self.generate_data_freshness_report,
            trigger=IntervalTrigger(hours=4),
            id="freshness_report",
            name="Data Freshness Report",
            max_instances=1
        )

        # Health check - runs every 5 minutes
        self.scheduler.add_job(
            func=self.health_check_job,
            trigger=IntervalTrigger(
                minutes=self.health_check_interval_minutes),
            id="health_check",
            name="System Health Check",
            max_instances=1
        )

        logger.info(f"Scheduled jobs configured:")
        logger.info(f"  - ETL Job: every {self.etl_interval_seconds} seconds")
        logger.info(f"  - Data Simulation: every 30 minutes")
        logger.info(f"  - Cleanup: daily at 2 AM")
        logger.info(f"  - Freshness Report: every 4 hours")
        logger.info(
            f"  - Health Check: every {self.health_check_interval_minutes} minutes")

    def start(self):
        """Start the scheduler"""
        logger.info("Starting Bus Data Pipeline Scheduler...")

        try:
            # Initial health checks
            logger.info("Performing initial health checks...")
            self.check_database_health()
            self.check_api_health()

            # Setup scheduled jobs
            self.setup_jobs()

            # Start scheduler
            logger.info("Scheduler started successfully")
            self.scheduler.start()

        except KeyboardInterrupt:
            logger.info("Scheduler interrupted by user")
        except Exception as e:
            logger.error(f"Scheduler failed to start: {e}")
            raise
        finally:
            logger.info("Shutting down scheduler...")
            if self.scheduler.running:
                self.scheduler.shutdown()


def main():
    """Entry point for scheduler service"""
    logger.info("Starting Bus Data Pipeline Scheduler Service")

    try:
        scheduler = BusDataScheduler()
        scheduler.start()

    except Exception as e:
        logger.error(f"Scheduler service failed: {e}")
        raise


if __name__ == "__main__":
    main()
