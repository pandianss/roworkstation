# RO Workstation

RO Workstation is an offline-first regional office banking operations dashboard for MIS analytics, compliance returns, document generation, branch coordination, knowledge management, and administrative workflows.

Built for Indian Public Sector Bank regional office teams, it combines a FastAPI backend service layer with a Next.js frontend web app, local repositories, and production-friendly deployment paths for restricted or internal network environments.

## Documentation

Detailed documentation is available in the `docs/` directory:

- **[Architecture](docs/architecture.md)**: Deep dive into the layered architecture and tech stack.
- **[User Guide](docs/user_guide.md)**: Comprehensive manual for Regional Office staff.
- **[Developer Guide](docs/developer_guide.md)**: Setup, standards, and how to extend the project.
- **[Deployment Guide](docs/deployment.md)**: Docker and offline deployment procedures.
- **[Data Hygiene](docs/data_hygiene.md)**: Source-control rules for runtime data, generated files, and operational archives.

## Quick Start

### Running Locally

To run the backend:
```bash
python -m uvicorn src.api.main:app --reload --port 8000
```

To run the frontend:
```bash
cd frontend
npm run dev
```

### Running with Docker

```bash
docker compose up --build
```

## Core Workflows

- **MIS Analytics**: Real-time KPIs and growth trends.
- **Document Centre**: Generate Office Notes, letters, and DD approvals.
- **Branch Coordination**: Track visits and campaign performance.
- **Knowledge Archive**: Global search and AI-powered QA on policy documents.
- **Compliance**: Manage DICGC and other statutory returns.

## Testing

The guaranteed test command uses Python's built-in `unittest` runner:

```bash
python -m unittest discover -s tests
```

With development dependencies installed:

```bash
pip install -r requirements-dev.txt
python -m pytest
```

---

*RO Workstation - Empowering Regional Operations with Data and Automation.*
