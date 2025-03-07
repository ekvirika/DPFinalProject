from typing import Generator

import pytest
from fastapi.testclient import TestClient

from infra.api.app import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Fixture for FastAPI test client."""
    client = TestClient(app)
    yield client
