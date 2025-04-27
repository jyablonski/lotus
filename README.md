# Lotus

Practice App w/ the following components

1. Next.js Frontend Application
2. Go Backend Service
    - gRPC Server
    - gRPC Gateway Server
    - HTTP Server (Legacy)
3. Postgres Database

## Running the App

To run the app, run `make up` to spin up all resources.

When finished, run `make down`.

## Architecture

``` mermaid
graph LR
    A[Frontend] -->|HTTP Request| B[gRPC Gateway]
    B -->|gRPC Request| C[gRPC Backend Service]
    C -->|Process Request| D[Database]
    C -->|gRPC Response| B
    B -->|HTTP Response| A

    subgraph Backend
        B[gRPC Gateway]
        C[gRPC Backend Service]
        D[Database]
    end

    subgraph Frontend
        A
    end

```