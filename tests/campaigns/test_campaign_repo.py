import uuid
from unittest.mock import MagicMock, Mock, patch

import pytest

from core.models.campaign import (
    BuyNGetNRule,
    Campaign,
    CampaignType,
    ComboRule,
    DiscountRule,
)
from core.models.errors import (
    CampaignNotFoundException,
)
from infra.db.database import Database
from infra.repositories.campaign_sqlite_repository import SQLiteCampaignRepository


@pytest.fixture
def mock_db() -> Mock:
    """Return a mock database."""
    mock_db = Mock(spec=Database)
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.__enter__.return_value = mock_connection
    mock_connection.cursor.return_value = mock_cursor
    mock_db.get_connection.return_value = mock_connection
    return mock_db


@pytest.fixture
def campaign_repository(mock_db: Mock) -> SQLiteCampaignRepository:
    """Return a campaign repository with a mock database."""
    return SQLiteCampaignRepository(mock_db)


def test_get_by_id_discount_campaign(
    campaign_repository: SQLiteCampaignRepository, mock_db: Mock
) -> None:
    """Test getting a discount campaign by ID."""
    # Arrange
    campaign_id = uuid.uuid4()
    rule_id = uuid.uuid4()

    # Set up the mock cursor for fetching data
    mock_cursor = (
        mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value
    )

    # Mock campaign data
    campaign_row = {
        "id": str(campaign_id),
        "name": "Summer Sale",
        "campaign_type": CampaignType.DISCOUNT.value,
        "is_active": 1,
    }

    # Mock rule data
    rule_row = {
        "id": str(rule_id),
        "campaign_id": str(campaign_id),
        "discount_value": 10.0,
        "applies_to": "all",
        "min_amount": 50.0,
    }

    # Set up the mock to return the expected data
    mock_cursor.fetchone.side_effect = [campaign_row, rule_row, None]
    mock_cursor.fetchall.return_value = []

    # Act
    campaign = campaign_repository.get_by_id(campaign_id)

    # Assert
    assert campaign.id == str(campaign_id)
    assert campaign.name == "Summer Sale"
    assert campaign.campaign_type == CampaignType.DISCOUNT
    assert campaign.is_active is True
    assert isinstance(campaign.rules, DiscountRule)
    assert campaign.rules.discount_value == 10.0
    assert campaign.rules.applies_to == "all"
    assert campaign.rules.min_amount == 50.0

    # Check DB calls
    mock_cursor.execute.assert_any_call(
        "SELECT * FROM campaigns WHERE id = ?", (str(campaign_id),)
    )
    mock_cursor.execute.assert_any_call(
        "SELECT * FROM discount_rules WHERE campaign_id = ?", (str(campaign_id),)
    )


def test_get_by_id_discount_campaign_with_products(
    campaign_repository: SQLiteCampaignRepository, mock_db: Mock
) -> None:
    """Test getting a discount campaign with product IDs by ID."""
    # Arrange
    campaign_id = uuid.uuid4()
    rule_id = uuid.uuid4()
    product_id_1 = str(uuid.uuid4())
    product_id_2 = str(uuid.uuid4())

    # Set up the mock cursor for fetching data
    mock_cursor = (
        mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value
    )

    # Mock campaign data
    campaign_row = {
        "id": str(campaign_id),
        "name": "Product Sale",
        "campaign_type": CampaignType.DISCOUNT.value,
        "is_active": 1,
    }

    # Mock rule data
    rule_row = {
        "id": str(rule_id),
        "campaign_id": str(campaign_id),
        "discount_value": 15.0,
        "applies_to": "product",
        "min_amount": None,
    }

    # Mock product IDs data
    product_rows = [{"product_id": product_id_1}, {"product_id": product_id_2}]

    # Set up the mock to return the expected data
    mock_cursor.fetchone.side_effect = [campaign_row, rule_row]
    mock_cursor.fetchall.return_value = product_rows

    # Act
    campaign = campaign_repository.get_by_id(campaign_id)

    # Assert
    assert campaign.id == str(campaign_id)
    assert campaign.name == "Product Sale"
    assert campaign.campaign_type == CampaignType.DISCOUNT
    assert campaign.is_active is True
    assert isinstance(campaign.rules, DiscountRule)
    assert campaign.rules.discount_value == 15.0
    assert campaign.rules.applies_to == "product"
    assert campaign.rules.product_ids == [product_id_1, product_id_2]

    # Check DB calls
    mock_cursor.execute.assert_any_call(
        "SELECT * FROM campaigns WHERE id = ?", (str(campaign_id),)
    )
    mock_cursor.execute.assert_any_call(
        "SELECT * FROM discount_rules WHERE campaign_id = ?", (str(campaign_id),)
    )
    mock_cursor.execute.assert_any_call(
        "SELECT product_id FROM discount_rule_products WHERE discount_rule_id = ?",
        (str(rule_id),),
    )


def test_get_by_id_buy_n_get_n_campaign(
    campaign_repository: SQLiteCampaignRepository, mock_db: Mock
) -> None:
    """Test getting a buy N get N campaign by ID."""
    # Arrange
    campaign_id = uuid.uuid4()
    rule_id = uuid.uuid4()
    buy_product_id = str(uuid.uuid4())
    get_product_id = str(uuid.uuid4())

    # Set up the mock cursor for fetching data
    mock_cursor = (
        mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value
    )

    # Mock campaign data
    campaign_row = {
        "id": str(campaign_id),
        "name": "Buy 2 Get 1 Free",
        "campaign_type": CampaignType.BUY_N_GET_N.value,
        "is_active": 1,
    }

    # Mock rule data
    rule_row = {
        "id": str(rule_id),
        "campaign_id": str(campaign_id),
        "buy_product_id": buy_product_id,
        "buy_quantity": 2,
        "get_product_id": get_product_id,
        "get_quantity": 1,
    }

    # Set up the mock to return the expected data
    mock_cursor.fetchone.side_effect = [campaign_row, rule_row]

    # Act
    campaign = campaign_repository.get_by_id(campaign_id)

    # Assert
    assert campaign.id == str(campaign_id)
    assert campaign.name == "Buy 2 Get 1 Free"
    assert campaign.campaign_type == CampaignType.BUY_N_GET_N
    assert campaign.is_active is True
    assert isinstance(campaign.rules, BuyNGetNRule)
    assert campaign.rules.buy_product_id == buy_product_id
    assert campaign.rules.buy_quantity == 2
    assert campaign.rules.get_product_id == get_product_id
    assert campaign.rules.get_quantity == 1

    # Check DB calls
    mock_cursor.execute.assert_any_call(
        "SELECT * FROM campaigns WHERE id = ?", (str(campaign_id),)
    )
    mock_cursor.execute.assert_any_call(
        "SELECT * FROM buy_n_get_n_rules WHERE campaign_id = ?", (str(campaign_id),)
    )


def test_get_by_id_combo_campaign(
    campaign_repository: SQLiteCampaignRepository, mock_db: Mock
) -> None:
    """Test getting a combo campaign by ID."""
    # Arrange
    campaign_id = uuid.uuid4()
    rule_id = uuid.uuid4()
    product_id_1 = str(uuid.uuid4())
    product_id_2 = str(uuid.uuid4())
    product_id_3 = str(uuid.uuid4())

    # Set up the mock cursor for fetching data
    mock_cursor = (
        mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value
    )

    # Mock campaign data
    campaign_row = {
        "id": str(campaign_id),
        "name": "Meal Deal",
        "campaign_type": CampaignType.COMBO.value,
        "is_active": 1,
    }

    # Mock rule data
    rule_row = {
        "id": str(rule_id),
        "campaign_id": str(campaign_id),
        "discount_type": "percentage",
        "discount_value": 20.0,
    }

    # Mock product IDs data
    product_rows = [
        {"product_id": product_id_1},
        {"product_id": product_id_2},
        {"product_id": product_id_3},
    ]

    # Set up the mock to return the expected data
    mock_cursor.fetchone.side_effect = [campaign_row, rule_row]
    mock_cursor.fetchall.return_value = product_rows

    # Act
    campaign = campaign_repository.get_by_id(campaign_id)

    # Assert
    assert campaign.id == str(campaign_id)
    assert campaign.name == "Meal Deal"
    assert campaign.campaign_type == CampaignType.COMBO
    assert campaign.is_active is True
    assert isinstance(campaign.rules, ComboRule)
    assert campaign.rules.product_ids == [product_id_1, product_id_2, product_id_3]
    assert campaign.rules.discount_type == "percentage"
    assert campaign.rules.discount_value == 20.0

    # Check DB calls
    mock_cursor.execute.assert_any_call(
        "SELECT * FROM campaigns WHERE id = ?", (str(campaign_id),)
    )
    mock_cursor.execute.assert_any_call(
        "SELECT * FROM combo_rules WHERE campaign_id = ?", (str(campaign_id),)
    )
    mock_cursor.execute.assert_any_call(
        "SELECT product_id FROM combo_rule_products WHERE combo_rule_id = ?",
        (str(rule_id),),
    )


def test_get_by_id_campaign_not_found(
    campaign_repository: SQLiteCampaignRepository, mock_db: Mock
) -> None:
    """Test getting a non-existent campaign by ID."""
    # Arrange
    campaign_id = uuid.uuid4()

    # Set up the mock cursor to return no data
    mock_cursor = (
        mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value
    )
    mock_cursor.fetchone.return_value = None

    # Act & Assert
    with pytest.raises(CampaignNotFoundException) as exc_info:
        campaign_repository.get_by_id(campaign_id)

    assert f"Campaign with ID '{campaign_id}' not found" in str(exc_info.value)

    # Check DB calls
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM campaigns WHERE id = ?", (str(campaign_id),)
    )


def test_get_all_campaigns(
    campaign_repository: SQLiteCampaignRepository, mock_db: Mock
) -> None:
    """Test getting all campaigns."""
    # Arrange
    campaign_id_1 = uuid.uuid4()
    campaign_id_2 = uuid.uuid4()

    # Set up the mock cursor to return campaign data
    mock_cursor = (
        mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value
    )
    mock_cursor.fetchall.return_value = [
        {
            "id": str(campaign_id_1),
            "name": "Campaign 1",
            "campaign_type": CampaignType.DISCOUNT.value,
            "is_active": 1,
        },
        {
            "id": str(campaign_id_2),
            "name": "Campaign 2",
            "campaign_type": CampaignType.BUY_N_GET_N.value,
            "is_active": 1,
        },
    ]

    # Mock get_by_id to return sample campaigns
    mock_campaign_1 = Campaign(
        id=str(campaign_id_1),
        name="Campaign 1",
        campaign_type=CampaignType.DISCOUNT,
        rules=DiscountRule(discount_value=10.0, applies_to="all"),
        is_active=True,
    )

    mock_campaign_2 = Campaign(
        id=str(campaign_id_2),
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

    # Patch the get_by_id method to return our mock campaigns
    with patch.object(
        SQLiteCampaignRepository,
        "get_by_id",
        side_effect=[mock_campaign_1, mock_campaign_2],
    ):
        # Act
        campaigns = campaign_repository.get_all()

    # Assert
    assert len(campaigns) == 2
    assert campaigns[0].id == str(campaign_id_1)
    assert campaigns[0].name == "Campaign 1"
    assert campaigns[1].id == str(campaign_id_2)
    assert campaigns[1].name == "Campaign 2"

    # Check DB calls
    mock_cursor.execute.assert_called_once_with("SELECT * FROM campaigns")


def test_deactivate_campaign(
    campaign_repository: SQLiteCampaignRepository, mock_db: Mock
) -> None:
    """Test deactivating a campaign."""
    # Arrange
    campaign_id = uuid.uuid4()

    # Set up the mock cursor
    mock_cursor = (
        mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value
    )
    mock_cursor.rowcount = 1  # Simulate that one row was updated

    # Act
    result = campaign_repository.deactivate(campaign_id)

    # Assert
    assert result is True

    # Check DB calls
    mock_cursor.execute.assert_called_once_with(
        "UPDATE campaigns SET is_active = 0 WHERE id = ?", (str(campaign_id),)
    )


def test_deactivate_campaign_not_found(
    campaign_repository: SQLiteCampaignRepository, mock_db: Mock
) -> None:
    """Test deactivating a non-existent campaign."""
    # Arrange
    campaign_id = uuid.uuid4()

    # Set up the mock cursor
    mock_cursor = (
        mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value
    )
    mock_cursor.rowcount = 0  # Simulate that no rows were updated

    # Act & Assert
    with pytest.raises(CampaignNotFoundException) as exc_info:
        campaign_repository.deactivate(campaign_id)

    assert f"Campaign with ID '{campaign_id}' not found" in str(exc_info.value)

    # Check DB calls
    mock_cursor.execute.assert_called_once_with(
        "UPDATE campaigns SET is_active = 0 WHERE id = ?", (str(campaign_id),)
    )


def test_get_active_campaigns(
    campaign_repository: SQLiteCampaignRepository, mock_db: Mock
) -> None:
    """Test getting active campaigns."""
    # Arrange
    campaign_id_1 = uuid.uuid4()
    campaign_id_2 = uuid.uuid4()

    # Set up the mock cursor to return active campaign data
    mock_cursor = (
        mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value
    )
    mock_cursor.fetchall.return_value = [
        {
            "id": str(campaign_id_1),
            "name": "Campaign 1",
            "campaign_type": CampaignType.DISCOUNT.value,
            "is_active": 1,
        },
        {
            "id": str(campaign_id_2),
            "name": "Campaign 2",
            "campaign_type": CampaignType.BUY_N_GET_N.value,
            "is_active": 1,
        },
    ]

    # Mock get_by_id to return sample campaigns
    mock_campaign_1 = Campaign(
        id=str(campaign_id_1),
        name="Campaign 1",
        campaign_type=CampaignType.DISCOUNT,
        rules=DiscountRule(discount_value=10.0, applies_to="all"),
        is_active=True,
    )

    mock_campaign_2 = Campaign(
        id=str(campaign_id_2),
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

    # Patch the get_by_id method to return our mock campaigns
    with patch.object(
        SQLiteCampaignRepository,
        "get_by_id",
        side_effect=[mock_campaign_1, mock_campaign_2],
    ):
        # Act
        campaigns = campaign_repository.get_active()

    # Assert
    assert len(campaigns) == 2
    assert campaigns[0].id == str(campaign_id_1)
    assert campaigns[0].name == "Campaign 1"
    assert campaigns[1].id == str(campaign_id_2)
    assert campaigns[1].name == "Campaign 2"

    # Check DB calls
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM campaigns WHERE is_active = 1"
    )
