FROM python:3.11

# Install system dependencies
RUN apt-get update && apt-get install -y libgl1-mesa-glx

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Command to run the application
CMD ["gunicorn", "--bind=0.0.0.0:8000", "--timeout", "600", "app:app"]
