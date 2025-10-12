#!/bin/bash

# wait_for_db.sh
echo "Waiting for MySQL database to be ready..."

while ! nc -z db 3306; do
  sleep 1
  echo "Still waiting for database..."
done

echo "MySQL database is ready!"