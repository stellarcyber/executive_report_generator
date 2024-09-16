# Use an official Python runtime as a parent image
FROM python:3.10-slim-bookworm

# Install system dependencies
RUN apt update && apt install -y weasyprint libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0

# Define a volume
VOLUME /app

# Set the working directory in the container to /app
WORKDIR /app

# Copy requirements.txt over to the container to install python dependencies
COPY ./requirements.txt /app/requirements.txt

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true

# Copy the current directory contents into the container at /app
# Later stage so code changes don't invalidate the cache
COPY . /app

# Make port 8501 available to the world outside this container
EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run app.py with streamlit when the container launches
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]