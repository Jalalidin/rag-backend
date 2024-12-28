# RAG-Backend: AI Chatbot with Document Retrieval

A scalable backend system for an AI chatbot that uses Retrieval-Augmented Generation (RAG) to provide accurate responses based on uploaded documents.

## Features

- Document upload and processing
- Asynchronous document indexing
- Real-time chat with AI
- Document-based context retrieval
- Scalable microservices architecture
- Support for multiple document formats

## System Architecture

The system consists of several microservices:
- **API Server**: Handles HTTP requests, user authentication, and chat interactions
- **Background Worker**: Processes documents and manages indexing
- **PostgreSQL**: Stores user data, document metadata, and chat history
- **Redis**: Handles caching and message queuing
- **Qdrant**: Vector database for document embeddings

## Prerequisites

- Python 3.10+ (3.12 recommended)
- Docker and Docker Compose
- Kubernetes (for production deployment)
- Git

## Development Setup

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd rag-backend
   ```

2. **Set Up Python Environment**
   ```bash
   pip install uv
   uv init
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   uv sync
   ```

3. **Configure Environment Variables**
   ```bash
   # Edit .env with your configuration
   ```

4. **Run with Docker Compose (Development)**
   ```bash
   docker-compose up --build
   ```

   This will start all necessary services:
   - API Server: http://localhost:8000
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379
   - Qdrant: http://localhost:6333

5. **API Documentation**
   - OpenAPI documentation: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Local Kubernetes Testing with Minikube

Before deploying to production, you can test the Kubernetes setup locally using Minikube.

1. **Install Minikube**
   
   Windows (PowerShell as Administrator):
   ```powershell
   # Install Minikube
   New-Item -Path 'c:\' -Name 'minikube' -ItemType Directory -Force
   Invoke-WebRequest -OutFile 'c:\minikube\minikube.exe' -Uri 'https://github.com/kubernetes/minikube/releases/latest/download/minikube-windows-amd64.exe'
   $oldPath = [Environment]::GetEnvironmentVariable('Path', [EnvironmentVariableTarget]::Machine)
   if ($oldPath.Split(';') -inotcontains 'C:\minikube'){ `
     [Environment]::SetEnvironmentVariable('Path', $('{0};C:\minikube' -f $oldPath), [EnvironmentVariableTarget]::Machine) `
   }

   # Install kubectl
   Invoke-WebRequest -OutFile 'C:\minikube\kubectl.exe' -Uri "https://dl.k8s.io/release/v1.28.0/bin/windows/amd64/kubectl.exe"
   ```

   macOS:
   ```bash
   # Install with Homebrew
   brew install minikube kubectl
   ```

   Linux:
   ```bash
   # Install Minikube
   curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
   sudo install minikube-linux-amd64 /usr/local/bin/minikube

   # Install kubectl
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
   ```

2. **Start Minikube**
   ```bash
   # Start Minikube cluster
   minikube start

   # Verify Minikube is running
   minikube status
   ```

3. **Configure Docker to Use Minikube's Registry**
   ```bash
   # For Unix-based systems (Linux/macOS)
   eval $(minikube docker-env)

   # For Windows PowerShell
   minikube docker-env | Invoke-Expression
   ```

4. **Build Images in Minikube**
   ```bash
   # Build API and Worker images
   docker build -t rag-backend-api:latest .
   docker build -t rag-backend-worker:latest .
   ```

   Note: Make sure you're using Minikube's Docker daemon (step 3) before building images.

5. **Deploy to Minikube**
   ```bash
   # Create namespace
   kubectl create namespace rag-backend

   # Apply Kubernetes configurations
   kubectl apply -k k8s/base
   ```

6. **Verify Deployment**
   ```bash
   # Check pod status
   kubectl get pods -n rag-backend

   # Check all resources
   kubectl get all -n rag-backend
   ```

7. **Access Services**
   ```bash
   # Port forward API server
   kubectl port-forward -n rag-backend service/api-server 8000:8000

   # Access the API at http://localhost:8000
   ```

8. **View Logs**
   ```bash
   # View logs for specific services
   kubectl logs -n rag-backend deployment/api-server
   kubectl logs -n rag-backend deployment/worker
   kubectl logs -n rag-backend deployment/postgres
   ```

9. **Cleanup**
   ```bash
   # Delete all resources
   kubectl delete namespace rag-backend

   # Stop Minikube
   minikube stop

   # Delete Minikube cluster if needed
   minikube delete
   ```

**Common Issues and Solutions:**

1. **ImagePullBackOff Error**
   - Symptom: Pods stuck in ImagePullBackOff state
   - Solution: Make sure to:
     1. Use Minikube's Docker daemon (`eval $(minikube docker-env)`)
     2. Build images with correct tags
     3. Set `imagePullPolicy: Never` in deployments

2. **Connection Issues**
   - Symptom: Can't pull images from Docker Hub
   - Solution: 
     1. Check internet connection
     2. Try `docker pull hello-world` to test connectivity
     3. Configure Docker proxy if behind corporate network

3. **Service Access Issues**
   - Symptom: Can't access services
   - Solution:
     1. Use `kubectl port-forward` to access services
     2. Check service and pod logs for specific errors
     3. Verify all pods are in Running state

4. **Volume Issues**
   - Symptom: Pods stuck in ContainerCreating state
   - Solution:
     1. Check PVC status: `kubectl get pvc -n rag-backend`
     2. Verify storage class availability
     3. Check pod events: `kubectl describe pod <pod-name> -n rag-backend`

## Production Deployment

### Prerequisites
- Kubernetes cluster
- kubectl configured
- Docker registry access

1. **Build and Push Docker Images**
   ```bash
   # Build images
   docker build -t your-registry/rag-backend-api:latest -f Dockerfile .
   docker build -t your-registry/rag-backend-worker:latest -f Dockerfile.worker .
   
   # Push to registry
   docker push your-registry/rag-backend-api:latest
   docker push your-registry/rag-backend-worker:latest
   ```

2. **Update Kubernetes Configurations**
   - Update image references in `k8s/base/deployment.yaml`
   - Configure secrets in `k8s/base/secrets.yaml`
   - Adjust resource requests in `k8s/base/persistent-volumes.yaml`

3. **Deploy to Kubernetes**
   ```bash
   # Create namespace
   kubectl create namespace rag-backend

   # Apply configurations
   kubectl apply -k k8s/base
   ```

4. **Verify Deployment**
   ```bash
   # Check pod status
   kubectl get pods -n rag-backend

   # Check services
   kubectl get services -n rag-backend
   ```

5. **Access the API**
   ```bash
   # Port forward the API service
   kubectl port-forward -n rag-backend service/api-server 8000:8000
   ```
