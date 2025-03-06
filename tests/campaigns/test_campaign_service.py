from typing import Any, Dict, List, Optional, cast
import uuid
from unittest.mock import Mock

import pytest

from core.models.campaign import Campaign, CampaignType, DiscountRule, BuyNGetNRule, ComboRule
from core.models.repositories.campaign_repository import CampaignRepository
from core.models.repositories.product_repository import ProductRepository
from core.services.campaign_service import CampaignService


@pytest.fixture
def mock_campaign_repository() -> Mock:
    """Return a mock campaign repository."""
    return Mock(spec=CampaignRepository)


@pytest.fixture
def mock_product_repository() -> Mock:
    """Return a mock product repository."""
    return Mock(spec=ProductRepository)


@pytest.fixture
def campaign_service(
        mock_campaign_repository: Mock, mock_product_repository: Mock
) -> CampaignService:
    """Return a campaign service with mock repositories."""
    return CampaignService(mock_campaign_repository, mock_product_repository)


def test_create_campaign(
        campaign_service: CampaignService, mock_campaign_repository: Mock
) -> None:
    """Test creating a campaign through the service layer."""
    # Arrange
    name = "Summer Sale"
    campaign_type = CampaignType.DISCOUNT.value
    rules = {
        "discount_value": 10.0,
        "applies_to": "all",
        "min_amount": 50.0,
    }

    # Mock repository response
    expected_campaign = Campaign(
        id=str(uuid.uuid4()),
        name=name,
        campaign_type=CampaignType.DISCOUNT,
        rules=DiscountRule(**rules),
        is_active=True
    )
    mock_campaign_repository.create.return_value = expected_campaign

    # Act
    result = campaign_service.create_campaign(name, campaign_type, rules)

    # Assert
    assert result == expected_campaign
    mock_campaign_repository.create.assert_called_once_with(name, campaign_type, rules)


def test_get_campaign(
        campaign_service: CampaignService, mock_campaign_repository: Mock
) -> None:
    """Test getting a campaign by ID through the service layer."""
    # Arrange
    campaign_id = uuid.uuid4()
    expected_campaign = Campaign(
        id=str(campaign_id),
        name="Test Campaign",
        campaign_type=CampaignType.DISCOUNT,
        rules=DiscountRule(discount_value=10.0, applies_to="all"),
        is_active=True
    )
    mock_campaign_repository.get_by_id.return_value = expected_campaign

    # Act
    result = campaign_service.get_campaign(campaign_id)

    # Assert
    assert result == expected_campaign
    mock_campaign_repository.get_by_id.assert_called_once_with(campaign_id)


def test_get_all_campaigns(
        campaign_service: CampaignService, mock_campaign_repository: Mock
) -> None:
    """Test getting all campaigns through the service layer."""
    # Arrange
    campaign_1 = Campaign(
        id=str(uuid.uuid4()),
        name="Campaign 1",
        campaign_type=CampaignType.DISCOUNT,
        rules=DiscountRule(discount_value=10.0, applies_to="all"),
        is_active=True
    )
    campaign_2 = Campaign(
        id=str(uuid.uuid4()),
        name="Campaign 2",
        campaign_type=CampaignType.BUY_N_GET_N,
        rules=BuyNGetNRule(
            buy_product_id=str(uuid.uuid4()),
            buy_quantity=2,
            get_product_id=str(uuid.uuid4()),
            get_quantity=1
        ),
        is_active=True
    )
    expected_campaigns = [campaign_1, campaign_2]
    mock_campaign_repository.get_all.return_value = expected_campaigns

    # Act
    result = campaign_service.get_all_campaigns()

    # Assert
    assert result == expected_campaigns
    mock_campaign_repository.get_all.assert_called_once()


def test_deactivate_campaign(
        campaign_service: CampaignService, mock_campaign_repository: Mock
) -> None:
    """Test deactivating a campaign through the service layer."""
    # Arrange
    campaign_id = uuid.uuid4()
    mock_campaign_repository.deactivate.return_value = True

    # Act
    campaign_service.deactivate_campaign(campaign_id)

    # Assert
    mock_campaign_repository.deactivate.assert_called_once_with(campaign_id)