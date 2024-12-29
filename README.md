# RAG-Backend: AI Chatbot with Document Retrieval

A scalable backend system for an AI chatbot that uses Retrieval-Augmented Generation (RAG) to provide accurate responses based on uploaded documents.

## Features

-   **Document Upload and Management:**
    -   Securely upload documents in various formats (PDF, DOCX, TXT, Markdown, HTML, CSV, XLSX).
    -   Manage uploaded documents with CRUD operations (Create, Read, Update, Delete).
-   **Asynchronous Document Processing:**
    -   Efficiently processes documents in the background using Celery and Redis.
    -   Tracks document processing status (Queued, Processing, Completed, Failed).
-   **Intelligent Indexing and Retrieval:**
    -   Extracts text and metadata from documents using advanced techniques.
    -   Generates embeddings using state-of-the-art models (OpenAI, Hugging Face Sentence Transformers).
    -   Stores embeddings in Qdrant, a high-performance vector database, for fast and accurate retrieval.
-   **Real-time AI Chat:**
    -   Provides a conversational interface powered by Large Language Models (LLMs).
    -   Supports multiple LLM providers (OpenAI, Google Gemini, Mistral, Claude, Llama, **OpenRouter**).
    -   Retrieves relevant document chunks to provide context-aware responses.
-   **User Authentication and Authorization:**
    -   Secure user authentication using JWT (JSON Web Tokens).
    -   Role-based access control to manage user permissions.
-   **Scalable Microservices Architecture:**
    -   Modular design with separate services for API, background workers, database, caching, and vector storage.
    -   Containerized using Docker for easy deployment and scaling.
    -   Kubernetes support for production-grade orchestration.
-   **API Documentation:**
    -   Comprehensive API documentation using OpenAPI (Swagger) and ReDoc.

## System Architecture

The system is built using a microservices architecture, comprising the following key components:

-   **API Server (FastAPI):**
    -   Handles HTTP requests and responses.
    -   Provides RESTful API endpoints for user authentication, document management, and chat interactions.
    -   Uses `uvicorn` as the ASGI server.
-   **Background Worker (Celery):**
    -   Processes documents asynchronously.
    -   Generates embeddings and stores them in Qdrant.
    -   Updates document status and metadata in the database.
-   **PostgreSQL:**
    -   Stores user data, document metadata, chat history, and LLM configurations.
    -   Uses Alembic for database migrations.
-   **Redis:**
    -   Acts as a message broker for Celery.
    -   Caches data for improved performance.
-   **Qdrant:**
    -   Vector database for storing and retrieving document embeddings.
    -   Enables fast and accurate similarity search.

## Technology Stack

-   **Programming Language:** Python 3.11
-   **Web Framework:** FastAPI
-   **Asynchronous Task Queue:** Celery
-   **Message Broker:** Redis
-   **Database:** PostgreSQL
-   **Vector Database:** Qdrant
-   **Authentication:** JWT
-   **Containerization:** Docker
-   **Orchestration:** Kubernetes (optional)
-   **LLM Libraries:** LangChain, LlamaIndex, **OpenRouter SDK**
-   **Embedding Models:** OpenAI, Hugging Face Sentence Transformers

## Prerequisites

-   Python 3.11+
-   Docker and Docker Compose
-   Git
-   (Optional) Kubernetes and kubectl for production deployment
-   (Optional) Minikube for local Kubernetes testing

## Development Setup

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/jalalidin/rag-backend.git
    cd rag-backend
    ```

2. **Set Up Python Environment:**

    ```bash
    pip install uv
    uv init
    uv sync
    ```

3. **Configure Environment Variables:**

    -   Create a `.env` file in the root directory.
    -   Add the following environment variables, providing your own API keys and configuration values:

    ```dotenv
    # Database Configuration
    POSTGRES_SERVER=db
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=your_postgres_password
    POSTGRES_DB=rag_chat_db
    DATABASE_URL=postgresql://postgres:your_postgres_password@db:5432/rag_chat_db

    # Redis Configuration
    REDIS_HOST=redis
    REDIS_PORT=6379
    REDIS_URL=redis://redis:6379/0

    # Qdrant Configuration
    QDRANT_HOST=qdrant
    QDRANT_PORT=6333
    QDRANT_URL=http://qdrant:6333
    QDRANT_COLLECTION_NAME=documents

    # API Keys (replace with your actual keys)
    OPENAI_API_KEY=your_openai_api_key
    GOOGLE_API_KEY=your_google_api_key
    MISTRAL_API_KEY=your_mistral_api_key
    ANTHROPIC_API_KEY=your_anthropic_api_key

    # Secret Key (generate a strong secret key)
    SECRET_KEY=your_secret_key

    # Embedding Model (choose one)
    # For OpenAI:
    EMBEDDING_MODEL=openai
    # For Hugging Face Sentence Transformers:
    # EMBEDDING_MODEL=huggingface:your_huggingface_model_name

    # Default LLM Model (choose one)
    # For OpenAI:
    DEFAULT_LLM_MODEL=gpt-3.5-turbo
    # For Google Gemini:
    # DEFAULT_LLM_MODEL=gemini-pro
    # For Mistral:
    # DEFAULT_LLM_MODEL=mistral-small
    # For Claude:
    # DEFAULT_LLM_MODEL=claude-3.5-sonnet
    # For Llama:
    # DEFAULT_LLM_MODEL=llama-3.2

    # Other Settings
    STARTUP_DELAY=5

    # OpenRouter Configuration (default key provided for convenience)
    OPENROUTER_API_KEY=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
    OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
    ```

4. **Run with Docker Compose (Development):**

    ```bash
    docker-compose up --build
    ```

    This command will:

    -   Build the Docker images for the API server, background worker, and Qdrant.
    -   Start containers for the API server, background worker, PostgreSQL, Redis, and Qdrant.

    Services will be accessible at the following URLs:

    -   **API Server:** <http://localhost:8000>
    -   **PostgreSQL:** `localhost:5432`
    -   **Redis:** `localhost:6379`
    -   **Qdrant:** <http://localhost:6333>

5. **API Documentation:**

    -   **OpenAPI (Swagger):** <http://localhost:8000/docs>
    -   **ReDoc:** <http://localhost:8000/redoc>

## Local Kubernetes Testing with Minikube

Before deploying to a production Kubernetes cluster, you can test the deployment locally using Minikube.

1. **Install Minikube and kubectl:**

    Follow the instructions for your operating system on the official Kubernetes website: [https://minikube.sigs.k8s.io/docs/start/](https://minikube.sigs.k8s.io/docs/start/)

2. **Start Minikube:**

    ```bash
    minikube start
    ```

3. **Configure Docker to Use Minikube's Registry:**

    ```bash
    eval $(minikube docker-env)
    ```

4. **Build Images in Minikube:**

    ```bash
    docker build -t rag-backend-api:latest .
    docker build -t rag-backend-worker:latest -f Dockerfile.worker .
    ```

5. **Deploy to Minikube:**

    ```bash
    kubectl create namespace rag-backend
    kubectl apply -k k8s/base
    ```

6. **Verify Deployment:**

    ```bash
    kubectl get pods -n rag-backend
    kubectl get all -n rag-backend
    ```

7. **Access Services:**

    ```bash
    kubectl port-forward -n rag-backend service/api-server 8000:8000
    ```

    The API will be accessible at <http://localhost:8000>.

8. **View Logs:**

    ```bash
    kubectl logs -n rag-backend deployment/api-server
    kubectl logs -n rag-backend deployment/worker
    kubectl logs -n rag-backend deployment/postgres
    ```

9. **Cleanup:**

    ```bash
    kubectl delete namespace rag-backend
    minikube stop
    minikube delete # Optional: Delete the Minikube cluster
    ```

## Production Deployment (Currently not implemented)

For production deployment, you'll need a Kubernetes cluster and a Docker registry.

1. **Build and Push Docker Images:**

    ```bash
    docker build -t your-registry/rag-backend-api:latest -f Dockerfile .
    docker build -t your-registry/rag-backend-worker:latest -f Dockerfile.worker .

    docker push your-registry/rag-backend-api:latest
    docker push your-registry/rag-backend-worker:latest
    ```

    Replace `your-registry` with your Docker registry (e.g., Docker Hub, Google Container Registry, AWS ECR).

2. **Update Kubernetes Configurations:**

    -   Modify `k8s/base/deployment.yaml` to use your image names from your registry.
    -   Update `k8s/base/secrets.yaml` with your production secrets.
    -   Adjust resource requests and limits in `k8s/base/deployment.yaml` and `k8s/base/persistent-volumes.yaml` as needed.

3. **Deploy to Kubernetes:**

    ```bash
    kubectl create namespace rag-backend
    kubectl apply -k k8s/base
    ```

4. **Verify Deployment:**

    ```bash
    kubectl get pods -n rag-backend
    kubectl get services -n rag-backend
    ```

5. **Access the API:**

    -   If you're using a LoadBalancer service, get the external IP:

        ```bash
        kubectl get service api-server -n rag-backend
        ```

    -   Alternatively, use port forwarding:

        ```bash
        kubectl port-forward -n rag-backend service/api-server 8000:8000
        ```

## Troubleshooting

**1. ImagePullBackOff Error:**

-   **Symptom:** Pods are stuck in the `ImagePullBackOff` state.
-   **Solution:**
    -   Ensure you are using Minikube's Docker daemon (`eval $(minikube docker-env)`).
    -   Build images with the correct tags.
    -   Set `imagePullPolicy: Never` in your deployments if using local images.

**2. Connection Issues:**

-   **Symptom:** Can't pull images from Docker Hub or other registries.
-   **Solution:**
    -   Check your internet connection.
    -   Test Docker Hub connectivity: `docker pull hello-world`
    -   Configure Docker proxy settings if you are behind a corporate network.

**3. Service Access Issues:**

-   **Symptom:** Can't access services deployed in Kubernetes.
-   **Solution:**
    -   Use `kubectl port-forward` to access services locally.
    -   Check service and pod logs for errors: `kubectl logs -n rag-backend <pod-name>`
    -   Verify that all pods are in the `Running` state.

**4. Volume Issues:**

-   **Symptom:** Pods are stuck in the `ContainerCreating` state.
-   **Solution:**
    -   Check PersistentVolumeClaim (PVC) status: `kubectl get pvc -n rag-backend`
    -   Verify that a storage class is available and configured correctly.
    -   Check pod events for details: `kubectl describe pod <pod-name> -n rag-backend`

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them with clear messages.
4. Write tests for your changes.
5. Submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
