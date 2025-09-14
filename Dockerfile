# Use Python 3.9 as the base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code and .env
COPY . .

# Expose port 33332
EXPOSE 33332

# Run Uvicorn with 4 workers for parallel handling
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "33332", "--workers", "4", "--loop", "uvloop"]
