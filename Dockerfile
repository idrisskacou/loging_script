# FROM python:3.9

# WORKDIR /app
# COPY script/requirements.txt requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt
# COPY script/ .

# CMD ["python", "log_parser.py"]

# Use an official Python image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy the script and requirements file
COPY script/log_parser.py /app/log_parser.py

# Install dependencies
RUN pip install psycopg2-binary python-dotenv

# Run the script
CMD ["python", "/app/log_parser.py"]
