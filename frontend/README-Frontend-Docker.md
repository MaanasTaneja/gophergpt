# GopherGPT Frontend Docker Deployment


OLD README PLEASE FIX....

This guide explains how to run just the GopherGPT frontend using Docker.

## 🐳 Frontend Docker Setup

### Prerequisites
- Docker installed on your system
- Backend running separately (or update API URL)

### Quick Start

**Option 1: Using the script (Recommended)**
```bash
./docker-run-frontend.sh
```

**Option 2: Manual commands**
```bash
# Build the image
docker build -t gophergpt-frontend .

# Run the container
docker run -d --name gophergpt-frontend -p 3000:3000 gophergpt-frontend
```

## 🏗️ Frontend Container Details

### Dockerfile
- **Base Image**: Node.js 18 Alpine (lightweight)
- **Build Process**: 
  - Installs dependencies
  - Builds production React app
  - Serves static files using `serve`
- **Port**: 3000
- **Size**: ~200MB (optimized)

### Build Steps
1. Copy `package.json` and install dependencies
2. Copy source code and configuration files
3. Build production React app (`npm run build`)
4. Install `serve` to serve static files
5. Start the server on port 3000

## 🔧 Configuration

### Environment Variables
The frontend uses environment variables for the API URL:

```bash
# Default API URL (if no env var set)
REACT_APP_API_URL=http://localhost:8000
```

### Custom API URL
If your backend is running on a different URL:

```bash
# Run with custom API URL
docker run -d --name gophergpt-frontend \
  -p 3000:3000 \
  -e REACT_APP_API_URL=http://your-backend-url:8000 \
  gophergpt-frontend
```

## 📦 Production Deployment

### Build for Production
```bash
# Build the image
docker build -t gophergpt-frontend .

# Tag for registry (optional)
docker tag gophergpt-frontend your-registry/gophergpt-frontend:latest

# Push to registry (optional)
docker push your-registry/gophergpt-frontend:latest
```

### Run in Production
```bash
# Run with production settings
docker run -d \
  --name gophergpt-frontend \
  -p 3000:3000 \
  -e REACT_APP_API_URL=https://your-api-domain.com \
  --restart unless-stopped \
  gophergpt-frontend
```

## 🚀 Scaling

### Multiple Instances
```bash
# Run multiple frontend instances
docker run -d --name gophergpt-frontend-1 -p 3000:3000 gophergpt-frontend
docker run -d --name gophergpt-frontend-2 -p 3001:3000 gophergpt-frontend
docker run -d --name gophergpt-frontend-3 -p 3002:3000 gophergpt-frontend
```

### With Load Balancer
Use nginx or another load balancer to distribute traffic across multiple frontend instances.

## 🔍 Troubleshooting

### Common Issues

1. **Container won't start:**
   ```bash
   # Check logs
   docker logs gophergpt-frontend
   
   # Check if port is already in use
   lsof -i :3000
   ```

2. **Frontend can't connect to backend:**
   - Verify backend is running
   - Check API URL environment variable
   - Ensure backend is accessible from frontend

3. **Build failures:**
   ```bash
   # Check build logs
   docker build -t gophergpt-frontend . --no-cache
   ```

### Useful Commands

```bash
# View logs
docker logs gophergpt-frontend

# Follow logs in real-time
docker logs -f gophergpt-frontend

# Stop container
docker stop gophergpt-frontend

# Start container
docker start gophergpt-frontend

# Remove container
docker rm gophergpt-frontend

# Remove image
docker rmi gophergpt-frontend

# List running containers
docker ps

# List all containers
docker ps -a
```

## 📝 Notes

- Frontend is built for production (optimized bundle)
- Uses `serve` to serve static files efficiently
- Container is stateless and can be easily scaled
- Image is based on Alpine Linux for smaller size
- All dependencies are installed during build time
- No need for Node.js on the host system

## 🌐 Access

Once running, access your application at:
**http://localhost:3000**
