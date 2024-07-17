FROM python:3.11

# Install dependencies
WORKDIR /usr/src/app

# Copy your application code
COPY . /usr/src/app

# Copy and make the wait_for_service.sh script executable
RUN chmod +x /usr/src/app/wait_for_service.sh

# Install netcat and any other needed packages specified in requirements.txt
RUN apt-get update && apt-get install -y netcat-openbsd && pip install --no-cache-dir -r requirements.txt


# Command to execute the wait script before starting your application
CMD ["/bin/bash", "-c", "./wait_for_service.sh db 5432 && python -m uvicorn main:app.api --host 0.0.0.0 --port 3000 --log-level debug --reload"]