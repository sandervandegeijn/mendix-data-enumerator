# Use the official Python 3.12 image from the Docker Hub
FROM python:3.12-slim

# Set environment variables to prevent Python from writing pyc files to disk and to force the output to be shown in the terminal
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip

# Install Playwright and Chromium
RUN pip install playwright \
    && playwright install-deps \
    && playwright install chromium

# Set the working directory
WORKDIR /app

# Copy the rest of the application code to the working directory
COPY webversion.py /app
COPY requirements.txt /app

# Install any remaining dependencies
RUN pip install -r requirements.txt

# Expose port 80 to the outside world
EXPOSE 80

# Command to run the Streamlit app
CMD ["streamlit", "run", "webversion.py", "--server.port=80"]