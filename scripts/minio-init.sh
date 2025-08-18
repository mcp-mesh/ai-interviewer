#!/bin/bash
# MinIO initialization script to set up bucket policies for internal access

# Wait for MinIO to be ready
sleep 10

# Configure MinIO client
mc alias set myminio http://minio:9000 minioadmin minioadmin123

# Create bucket if it doesn't exist
mc mb myminio/ai-interviewer-uploads --ignore-existing

# Set bucket policy to allow anonymous read access for the entire bucket
mc anonymous set download myminio/ai-interviewer-uploads

# Optionally, create a public policy for uploads too (if needed in the future)
# mc anonymous set upload myminio/ai-interviewer-uploads

echo "MinIO bucket ai-interviewer-uploads configured for anonymous download access"