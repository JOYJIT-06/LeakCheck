import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Return the repository root directory as a resolved Path object."""
    return Path(__file__).resolve().parents[1]

