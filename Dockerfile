# Use an official Python runtime as a parent image
FROM python:3.11-slim-bullseye

# Set environment variables to prevent generating .pyc files and to buffer output
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create a non-root user and group
RUN addgroup --system app && adduser --system --ingroup app app

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed dependencies specified in requirements.txt
# Using --no-cache-dir makes the image smaller
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's source code from the host to the container
COPY . .

# Change the ownership of the application files to the non-root user
RUN chown -R app:app /app

# Switch to the non-root user
USER app

# Expose the port the app runs on (default for FastAPI/Uvicorn is 8000)
EXPOSE 8000

# Define the command to run the application
# The command runs Uvicorn, a fast ASGI server.
# It listens on all network interfaces (0.0.0.0) on port 8000.
# Adjust 'main:app' if your main application file or FastAPI instance is named differently.
# For example, if your file is 'src/app.py' and the instance is 'server', use:
# CMD ["uvicorn", "src.app:server", "--host", "0.0.0.0", "--port", "8000"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]