FROM openjdk:11-jre-slim

# Install Python and required system packages
RUN apt-get update && apt-get install -y \
  python3 \
  python3-pip \
  python3-dev \
  wget \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Download PostgreSQL JDBC driver
RUN wget https://jdbc.postgresql.org/download/postgresql-42.6.0.jar -O /opt/postgresql-42.6.0.jar

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

# Configure Spark to use PostgreSQL JDBC driver
ENV SPARK_CLASSPATH=/opt/postgresql-42.6.0.jar

# Create data directories
RUN mkdir -p /app/data/raw /app/data/processed /app/data/error

# Run the ETL job
CMD ["python3", "etl_job.py"] 