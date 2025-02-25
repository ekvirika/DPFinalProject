from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from runner.dependencies import AppContainer, get_app_container


# ------------------------ DATABASE CONFIGURATION ------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ------------------------ OVERRIDES ------------------------
def override_get_app_container() -> AppContainer:
    """Override the app container to use an in-memory database."""
    container = AppContainer()
    container.database_url.override(SQLALCHEMY_DATABASE_URL)  # Override the database URL
    return container


# ------------------------ FIXTURES ------------------------
@pytest.fixture(scope="function")
def db_session():
    """Set up and tear down the database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Fixture for FastAPI test client."""
    app.dependency_overrides[get_app_container] = override_get_app_container
    return TestClient(app)
