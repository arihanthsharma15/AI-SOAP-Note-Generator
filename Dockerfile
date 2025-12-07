# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --default-timeout=100 -r requirements.txt

# Copy the rest of the application's code to the working directory
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define the command to run the app using uvicorn
# It will listen on all available IPs (0.0.0.0)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]