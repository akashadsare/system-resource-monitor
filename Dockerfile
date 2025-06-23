# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY system_monitor.py ./
COPY optimize.sh ./

# Make the scripts executable
RUN chmod +x system_monitor.py optimize.sh

# Default command (can be overridden)
CMD ["python", "system_monitor.py", "--help"] 