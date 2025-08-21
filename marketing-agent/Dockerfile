# Use an official Python 3.11 slim runtime as a parent image
# This provides a lightweight and secure base.
FROM python:3.11-slim

# Set environment variables to ensure logs are sent straight to the console
# and to prevent Python from writing .pyc files.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container to /app
WORKDIR /app

# Copy the requirements file first to leverage Docker layer caching.
# Dependencies will only be re-installed if requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire 'app' directory into the container at /app
COPY ./app /app

# Expose port 8080 to allow communication with the app
EXPOSE 8080

# Command to run the application using the ADK's built-in web server.
# This server automatically discovers the 'root_agent' in the specified module,
# serves the API, and provides a web-based test UI.
CMD ["adk", "web", "main:root_agent", "--host", "0.0.0.0", "--port", "8080"]
