# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the application code
COPY . /app

# Expose the port the app runs on
EXPOSE 5000

# Set the entry point to run the app
CMD ["flask", "--app=run", "run", "--host=0.0.0.0", "--port=5000"]
