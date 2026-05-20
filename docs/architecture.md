# Project Architecture

RO Workstation is designed with a layered architecture to ensure separation of concerns, maintainability, and scalability. It follows a modular structure where each layer has a specific responsibility.

## Layer Overview

The project is organized into the following layers:

### 1. Core Layer (`src/core`)
The foundation of the application, providing cross-cutting concerns:
- **Config**: Centralized configuration management with caching (`config_loader.py`).
- **Security**: Authentication, session handling, and role-based access control.
- **Logging**: Unified logging utilities.
- **Paths**: Path management for different environments.
- **Registry**: Component and service registration.

### 2. Domain Layer (`src/domain`)
Contains the business logic and data structures:
- **Entities**: Core business objects.
- **Models**: Pydantic models for data validation and serialization.
- **Schemas**: Data transfer objects and API schemas.

### 3. Application Layer (`src/application`)
Implements the business use cases and services:
- **Services**: Business logic for specific modules (MIS, DICGC, Office Note, etc.).
- **Use Cases**: Orchestration of services to fulfill specific user actions.

### 4. Infrastructure Layer (`src/infrastructure`)
Handles technical details and external integrations:
- **Persistence**: Repositories for data storage (SQLite, JSON, Excel).
- **Loaders**: Data ingestion from various sources.
- **LLM**: Adapters for Large Language Models (e.g., Ollama/Mistral for knowledge management).
- **Templates**: Jinja2 templates for document generation.

### 5. Interface Layer (`src/interface`)
The presentation layer, built with Streamlit:
- **Pages**: Individual Streamlit pages representing different modules.
- **Components**: Reusable UI components.
- **Theme**: Visual styling and layout configuration.
- **State**: Management of user session and application state.

## Data Flow

1. **User Interaction**: The user interacts with the **Interface** layer (Streamlit).
2. **Request Processing**: The interface calls the appropriate **Application Service**.
3. **Business Logic**: The service applies business rules, often using **Domain Models** for validation.
4. **Data Access**: The service uses **Infrastructure Repositories** to fetch or persist data.
5. **Response**: The result is returned through the layers back to the **Interface** for display.

## Technology Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **Logic**: Python 3.x
- **Data Validation**: [Pydantic](https://docs.pydantic.dev/)
- **Templating**: [Jinja2](https://palletsprojects.com/p/jinja/)
- **Database**: SQLite (via SQLAlchemy), JSON, Excel
- **Deployment**: Docker, Docker Compose
- **NLP/AI**: Ollama (for offline LLM), Sentence Transformers
