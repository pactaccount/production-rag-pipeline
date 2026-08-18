# Stage 1: Build the React frontend
FROM node:22-alpine AS build-stage
WORKDIR /frontend
# Copy package files and install dependencies
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
# Copy the rest of the frontend code and build
COPY frontend/ ./
RUN npm run build

# Stage 2: Build the Python backend
FROM python:3.12-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user for Hugging Face Spaces
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copy the backend application code
COPY --chown=user . $HOME/app

# Copy the built frontend from Stage 1
COPY --from=build-stage --chown=user /frontend/dist $HOME/app/frontend/dist

# Expose port 7860
EXPOSE 7860

# Run FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
