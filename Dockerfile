# Use the official Python image
FROM python:3.9-slim

# Set environment variables
ARG API_KEY
ENV API_KEY=${API_KEY}

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Command to run the application
CMD ["python", "app.py"]
