# Etapa 1: compilar
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o ms2-server .

# Etapa 2: imagen final mínima
FROM alpine:3.19
WORKDIR /app
COPY --from=builder /app/ms2-server .
EXPOSE 8002
CMD ["./ms2-server"]
