# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables to prevent buffering and bytecode files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY ./app /app

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application using the ADK's web server
# This automatically discovers and serves the agent defined in main.py
CMD ["adk", "web", "--host", "0.0.0.0", "--port", "8080"]
