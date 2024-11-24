#!/bin/sh

CPU_CORES=$(nproc)

echo "Starting Locust cluster with $CPU_CORES workers (based on CPU cores)..."
echo "Locust cluster is running."
echo "Master UI available at: http://localhost:8089"

docker-compose up --scale worker="$CPU_CORES"
