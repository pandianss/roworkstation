from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def project_path(*parts: str) -> Path:
    """Return an absolute path rooted at the repository."""
    return PROJECT_ROOT.joinpath(*parts)
