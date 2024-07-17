#!/bin/bash
# Usage: ./wait_for_service.sh host port

host=$1
port=$2
max_attempts=15
attempt_counter=0
sleep_seconds=5

echo "Waiting for $host:$port to be available..."

while ! nc -z $host $port; do
    if [ ${attempt_counter} -eq ${max_attempts} ]; then
      echo "Max attempts reached, unable to connect to $host:$port"
      exit 1
    fi

    echo "Trying to connect to $host:$port (attempt: $((attempt_counter+1))/$max_attempts)"
    attempt_counter=$((attempt_counter+1))
    sleep $sleep_seconds
done

echo "$host:$port is available."
