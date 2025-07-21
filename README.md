# Lotus

Practice App w/ the following components

1. Next.js Frontend Application
2. Go Backend Service
    - gRPC Server
    - gRPC Gateway Server
3. Python Journal Analyzer Service
    - HTTP Server
4. Postgres Database

## Running the App

To run the app, run `make up` to spin up all resources.

When finished, run `make down`.

## Architecture

``` mermaid
graph LR
    A[NextJS] -->|HTTP Request| B[Go gRPC Gateway]
    B -->|gRPC Request| C[gRPC Backend Service]
    C --> D[Postgres Database]
    D --> C
    C -->|gRPC Response| B
    B -->|HTTP Response| A

    C -->|HTTP Request| E[Python Text Analyzer Service]
    E --> D

    subgraph Backend
        B[gRPC Gateway]
        C[gRPC Backend Service]
        D[Postgres Database]
        E[Python Text Analyzer Service]
    end

    subgraph Frontend
        A
    end

```