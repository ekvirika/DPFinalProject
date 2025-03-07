import uuid
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from core.models.campaign import (
    BuyNGetNRule,
    Campaign,
    CampaignType,
    DiscountRule,
)
from core.models.errors import CampaignNotFoundException, InvalidCampaignRulesException
from core.services.campaign_service import CampaignService
from infra.api.routers.campaign_router import router
from runner.dependencies import get_campaign_service


@pytest.fixture
def mock_campaign_service() -> Mock:
    """Return a mock campaign service."""
    return Mock(spec=CampaignService)


@pytest.fixture
def client(mock_campaign_service: Mock) -> TestClient:
    """Test client with mocked dependencies."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router, prefix="/campaigns")

    # Override dependency
    app.dependency_overrides = {get_campaign_service: lambda: mock_campaign_service}

    return TestClient(app)


def test_create_campaign(client: TestClient, mock_campaign_service: Mock) -> None:
    """Test creating a campaign via the API."""
    # Arrange
    campaign_id = str(uuid.uuid4())
    request_data = {
        "name": "Summer Sale",
        "campaign_type": "discount",
        "rules": {"discount_value": 10.0, "applies_to": "all", "min_amount": 50.0},
    }

    # Mock service response
    mock_campaign = Campaign(
        id=campaign_id,
        name="Summer Sale",
        campaign_type=CampaignType.DISCOUNT,
        rules=DiscountRule(discount_value=10.0, applies_to="all", min_amount=50.0),
        is_active=True,
    )
    mock_campaign_service.create_campaign.return_value = mock_campaign

    # Act
    response = client.post("/campaigns/", json=request_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "campaign" in data
    campaign = data["campaign"]
    assert campaign["id"] == campaign_id
    assert campaign["name"] == "Summer Sale"
    assert campaign["campaign_type"] == "discount"
    assert campaign["rules"]["discount_value"] == 10.0
    assert campaign["rules"]["applies_to"] == "all"
    assert campaign["rules"]["min_amount"] == 50.0
    assert campaign["is_active"] is True

    # Check service calls
    mock_campaign_service.create_campaign.assert_called_once_with(
        "Summer Sale",
        "discount",
        {"discount_value": 10.0, "applies_to": "all", "min_amount": 50.0},
    )


def test_create_campaign_with_invalid_rules(
    client: TestClient, mock_campaign_service: Mock
) -> None:
    """Test creating a campaign with invalid rules via the API."""
    # Arrange
    request_data = {
        "name": "Summer Sale",
        "campaign_type": "discount",
        "rules": {
            "discount_value": -10.0,  # Invalid negative value
            "applies_to": "all",
        },
    }

    # Mock service to raise an exception
    mock_campaign_service.create_campaign.side_effect = InvalidCampaignRulesException(
        "Discount value cannot be negative"
    )

    # Act
    response = client.post("/campaigns/", json=request_data)

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "400: Discount value cannot be negative"

    # Check service calls
    mock_campaign_service.create_campaign.assert_called_once()


def test_get_campaign(client: TestClient, mock_campaign_service: Mock) -> None:
    """Test getting a campaign by ID via the API."""
    # Arrange
    campaign_id = uuid.uuid4()

    # Mock service response
    mock_campaign = Campaign(
        id=str(campaign_id),
        name="Test Campaign",
        campaign_type=CampaignType.DISCOUNT,
        rules=DiscountRule(discount_value=10.0, applies_to="all"),
        is_active=True,
    )
    mock_campaign_service.get_campaign.return_value = mock_campaign

    # Act
    response = client.get(f"/campaigns/{campaign_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "campaign" in data
    campaign = data["campaign"]
    assert campaign["id"] == str(campaign_id)
    assert campaign["name"] == "Test Campaign"
    assert campaign["campaign_type"] == "discount"
    assert campaign["rules"]["discount_value"] == 10.0
    assert campaign["rules"]["applies_to"] == "all"
    assert campaign["is_active"] is True

    # Check service calls
    mock_campaign_service.get_campaign.assert_called_once_with(campaign_id)


def test_get_campaign_not_found(
    client: TestClient, mock_campaign_service: Mock
) -> None:
    """Test getting a non-existent campaign by ID via the API."""
    # Arrange
    campaign_id = uuid.uuid4()

    # Mock service to raise an exception
    mock_campaign_service.get_campaign.side_effect = CampaignNotFoundException(
        str(campaign_id)
    )

    # Act
    response = client.get(f"/campaigns/{campaign_id}")

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"] == f"404: Campaign with ID '{campaign_id}' not found"

    # Check service calls
    mock_campaign_service.get_campaign.assert_called_once_with(campaign_id)


def test_list_campaigns(client: TestClient, mock_campaign_service: Mock) -> None:
    """Test listing all campaigns via the API."""
    # Arrange
    campaign_1 = Campaign(
        id=str(uuid.uuid4()),
        name="Campaign 1",
        campaign_type=CampaignType.DISCOUNT,
        rules=DiscountRule(discount_value=10.0, applies_to="all"),
        is_active=True,
    )
    campaign_2 = Campaign(
        id=str(uuid.uuid4()),
        name="Campaign 2",
        campaign_type=CampaignType.BUY_N_GET_N,
        rules=BuyNGetNRule(
            buy_product_id=str(uuid.uuid4()),
            buy_quantity=2,
            get_product_id=str(uuid.uuid4()),
            get_quantity=1,
        ),
        is_active=True,
    )

    # Mock service response
    mock_campaign_service.get_all_campaigns.return_value = [campaign_1, campaign_2]

    # Act
    response = client.get("/campaigns/")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "campaigns" in data
    campaigns = data["campaigns"]
    assert len(campaigns) == 2

    # Check first campaign
    assert campaigns[0]["id"] == campaign_1.id
    assert campaigns[0]["name"] == "Campaign 1"
    assert campaigns[0]["campaign_type"] == "discount"

    # Check second campaign
    assert campaigns[1]["id"] == campaign_2.id
    assert campaigns[1]["name"] == "Campaign 2"
    assert campaigns[1]["campaign_type"] == "buy_n_get_n"

    # Check service calls
    mock_campaign_service.get_all_campaigns.assert_called_once()


def test_deactivate_campaign(client: TestClient, mock_campaign_service: Mock) -> None:
    """Test deactivating a campaign via the API."""
    # Arrange
    campaign_id = uuid.uuid4()

    # Act
    response = client.delete(f"/campaigns/{campaign_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # Check service calls
    mock_campaign_service.deactivate_campaign.assert_called_once_with(campaign_id)


def test_deactivate_campaign_not_found(
    client: TestClient, mock_campaign_service: Mock
) -> None:
    """Test deactivating a non-existent campaign via the API."""
    # Arrange
    campaign_id = uuid.uuid4()

    # Mock service to raise an exception
    mock_campaign_service.deactivate_campaign.side_effect = CampaignNotFoundException(
        str(campaign_id)
    )

    # Act
    response = client.delete(f"/campaigns/{campaign_id}")

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"] == f"404: Campaign with ID '{campaign_id}' not found"

    # Check service calls
    mock_campaign_service.deactivate_campaign.assert_called_once_with(campaign_id)
