# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Expose port 8002 for FastAPI
EXPOSE 8002

# Run the uvicorn server with FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]