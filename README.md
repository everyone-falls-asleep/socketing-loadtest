# socketing-loadtest

This repository contains a distributed load testing setup using Locust. The configuration supports both HTTP and WebSocket scenarios, enabling scalability with multiple worker nodes.

## Prerequisites

- Docker
- Docker Compose

## Getting Started

### Configure Environment

First, create a .env file based on the provided .env.example template:

```bash
cp .env.example .env
```

Edit the .env file to set your target URL and other configurations:

```bash
TARGET_API_SERVER="https://your-target-url"
TARGET_SOCKET_SERVER="https://your-target-url"
EVENT_ID="example-event-id"
EVENT_DATE_ID="example-event-date-id"
```

### Run the Locust Cluster

Once the .env file is configured, use the provided run.sh script to start the Locust cluster. This script automatically scales the workers based on the system's CPU cores:

```bash
./run.sh
```

The Locust Web UI will be available at: http://localhost:8089
