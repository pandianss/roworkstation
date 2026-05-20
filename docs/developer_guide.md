# Developer Guide

Welcome to the RO Workstation development team! This guide will help you set up your environment and understand the development workflows.

## Getting Started

### Prerequisites
- Python 3.9 or higher
- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/)
- [Ollama](https://ollama.ai/) (optional, for LLM-powered features)

### Local Environment Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ro_workstation
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   For tests and formatting tools:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Set up environment variables**:
   Copy `.env.example` to `.env` and configure as needed.

5. **Run the application**:
   ```bash
   python -m streamlit run app.py
   ```

## Development Standards

### Coding Style
- We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code.
- Use `black` for code formatting.
- Use `isort` to sort imports.
- Use `flake8` for linting.

### Testing
- The guaranteed test command uses Python's built-in `unittest` runner.
- `pytest` is supported when `requirements-dev.txt` is installed.
- Tests are located in the `tests/` directory.
- Run tests with: `python -m unittest discover -s tests`
- Optional pytest command: `python -m pytest`

## Adding a New Module

To add a new feature or module, follow these steps:

1. **Define the Domain**: Add any new Pydantic models in `src/domain/models/`.
2. **Create a Service**: Implement the business logic in a new service class in `src/application/services/`.
3. **Implement Repository**: If data persistence is needed, add a repository in `src/infrastructure/persistence/`.
4. **Build the Interface**: Create a new Streamlit page in `src/interface/streamlit/pages/`.
5. **Register Components**: If you created reusable UI elements, add them to `src/interface/streamlit/components/`.

## Working with Document Templates

- Templates are stored in `src/infrastructure/templates/`.
- We use **Jinja2** for HTML/LaTeX templates.
- Ensure all templates are trilingual where applicable (English, Hindi, Tamil).

## Core Utilities

- Use `src/core/config/config_loader.py` for all configuration needs.
- Use `src/core/logging/` for unified logging.
- Use `src/core/paths.py` for consistent file path management across different environments.
