FROM golang:1.24-alpine AS builder

RUN go install github.com/air-verse/air@latest

# ---- Final image ----
# need to use golang:1.24 instead of slimmer image for glibc
# because of the air binary
FROM golang:1.24-alpine

COPY --from=builder /go/bin/air /usr/local/bin/air

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download
COPY . .

EXPOSE 8080 50051

# Start the app with Air
CMD ["air", "-c", ".air.toml"]
