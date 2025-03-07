import uuid
from unittest.mock import Mock

import pytest

from core.models.errors import ShiftNotFoundError
from core.models.receipt import (
    Currency,
    Payment,
    PaymentStatus,
    Quote,
    Receipt,
    ReceiptItem,
    ReceiptStatus,
)
from core.models.repositories.payment_repository import PaymentRepository
from core.models.repositories.product_repository import ProductRepository
from core.models.repositories.receipt_repository import ReceiptRepository
from core.models.repositories.shift_repository import ShiftRepository
from core.models.shift import ShiftStatus
from core.services.discount_service import DiscountService
from core.services.exchange_rate_service import ExchangeRateService
from core.services.receipt_service import ReceiptService


@pytest.fixture
def mock_receipt_repository() -> Mock:
    """Return a mock receipt repository."""
    return Mock(spec=ReceiptRepository)


@pytest.fixture
def mock_product_repository() -> Mock:
    """Return a mock product repository."""
    return Mock(spec=ProductRepository)


@pytest.fixture
def mock_shift_repository() -> Mock:
    """Return a mock shift repository."""
    return Mock(spec=ShiftRepository)


@pytest.fixture
def mock_discount_service() -> Mock:
    """Return a mock discount service."""
    return Mock(spec=DiscountService)


@pytest.fixture
def mock_exchange_service() -> Mock:
    """Return a mock exchange rate service."""
    return Mock(spec=ExchangeRateService)


@pytest.fixture
def mock_payment_repository() -> Mock:
    """Return a mock payment repository."""
    return Mock(spec=PaymentRepository)


@pytest.fixture
def receipt_service(
    mock_receipt_repository: Mock,
    mock_product_repository: Mock,
    mock_shift_repository: Mock,
    mock_discount_service: Mock,
    mock_exchange_service: Mock,
    mock_payment_repository: Mock,
) -> ReceiptService:
    """Return a receipt service with mock dependencies."""
    return ReceiptService(
        mock_receipt_repository,
        mock_product_repository,
        mock_shift_repository,
        mock_discount_service,
        mock_exchange_service,
        mock_payment_repository,
    )


def test_create_receipt_shift_not_found(
    receipt_service: ReceiptService,
    mock_shift_repository: Mock,
) -> None:
    """Test creating a receipt for a non-existent shift."""
    # Arrange
    shift_id = uuid.uuid4()

    # Mock shift doesn't exist
    mock_shift_repository.get_by_id.return_value = None

    # Act
    result = receipt_service.create_receipt(shift_id)

    # Assert
    assert result is None
    mock_shift_repository.get_by_id.assert_called_once_with(shift_id)


def test_get_receipt(
    receipt_service: ReceiptService,
    mock_receipt_repository: Mock,
) -> None:
    """Test getting a receipt by ID."""
    # Arrange
    receipt_id = uuid.uuid4()
    expected_receipt = Receipt(shift_id=uuid.uuid4(), id=receipt_id)
    mock_receipt_repository.get.return_value = expected_receipt

    # Act
    result = receipt_service.get_receipt(receipt_id)

    # Assert
    assert result == expected_receipt
    mock_receipt_repository.get.assert_called_once_with(receipt_id)


def test_add_product_existing_item(
    receipt_service: ReceiptService,
    mock_receipt_repository: Mock,
    mock_product_repository: Mock,
    mock_discount_service: Mock,
) -> None:
    """Test adding more of an existing product to a receipt."""
    # Arrange
    receipt_id = uuid.uuid4()
    product_id = uuid.uuid4()
    initial_quantity = 1
    additional_quantity = 2

    # Mock receipt with existing item
    existing_item = ReceiptItem(
        product_id=product_id,
        quantity=initial_quantity,
        unit_price=10.0,
    )
    receipt = Receipt(
        shift_id=uuid.uuid4(),
        id=receipt_id,
        products=[existing_item],
        subtotal=10.0,
        total=10.0,
    )
    mock_receipt_repository.get.return_value = receipt

    # Mock product
    product = {"id": product_id, "name": "Test Product", "price": 10.0}
    mock_product_repository.get_by_id.return_value = product

    # Mock updated receipt with increased quantity
    updated_receipt = Receipt(
        shift_id=receipt.shift_id,
        id=receipt_id,
        products=[
            ReceiptItem(
                product_id=product_id,
                quantity=initial_quantity + additional_quantity,
                unit_price=10.0,
            )
        ],
        subtotal=30.0,
        total=30.0,
    )

    # Mock discount service
    mock_discount_service.apply_discounts.return_value = updated_receipt

    # Mock repository update
    mock_receipt_repository.update.return_value = updated_receipt

    # Act
    result = receipt_service.add_product(receipt_id, product_id, additional_quantity)

    # Assert
    assert result == updated_receipt
    assert result.products[0].product_id == product_id
    assert result.products[0].quantity == initial_quantity + additional_quantity

    mock_receipt_repository.get.assert_called_once_with(receipt_id)
    mock_product_repository.get_by_id.assert_called_once_with(product_id)
    mock_discount_service.apply_discounts.assert_called_once()
    mock_receipt_repository.update.assert_called_once_with(receipt_id, updated_receipt)


def test_add_product_receipt_not_found(
    receipt_service: ReceiptService,
    mock_receipt_repository: Mock,
) -> None:
    """Test adding a product to a non-existent receipt."""
    # Arrange
    receipt_id = uuid.uuid4()
    product_id = uuid.uuid4()
    quantity = 2

    # Mock receipt not found
    mock_receipt_repository.get.return_value = None

    # Act
    result = receipt_service.add_product(receipt_id, product_id, quantity)

    # Assert
    assert result is None
    mock_receipt_repository.get.assert_called_once_with(receipt_id)


def test_add_product_closed_receipt(
    receipt_service: ReceiptService,
    mock_receipt_repository: Mock,
) -> None:
    """Test adding a product to a closed receipt."""
    # Arrange
    receipt_id = uuid.uuid4()
    product_id = uuid.uuid4()
    quantity = 2

    # Mock closed receipt
    receipt = Receipt(
        shift_id=uuid.uuid4(),
        id=receipt_id,
        status=ReceiptStatus.CLOSED,
    )
    mock_receipt_repository.get.return_value = receipt

    # Act
    result = receipt_service.add_product(receipt_id, product_id, quantity)

    # Assert
    assert result is None
    mock_receipt_repository.get.assert_called_once_with(receipt_id)


def test_add_product_product_not_found(
    receipt_service: ReceiptService,
    mock_receipt_repository: Mock,
    mock_product_repository: Mock,
) -> None:
    """Test adding a non-existent product to a receipt."""
    # Arrange
    receipt_id = uuid.uuid4()
    product_id = uuid.uuid4()
    quantity = 2

    # Mock receipt
    receipt = Receipt(shift_id=uuid.uuid4(), id=receipt_id)
    mock_receipt_repository.get.return_value = receipt

    # Mock product not found
    mock_product_repository.get_by_id.return_value = None

    # Act
    result = receipt_service.add_product(receipt_id, product_id, quantity)

    # Assert
    assert result is None
    mock_receipt_repository.get.assert_called_once_with(receipt_id)
    mock_product_repository.get_by_id.assert_called_once_with(product_id)


def test_remove_product_complete_removal(
    receipt_service: ReceiptService,
    mock_receipt_repository: Mock,
    mock_discount_service: Mock,
) -> None:
    """Test completely removing a product from a receipt."""
    # Arrange
    receipt_id = uuid.uuid4()
    product_id = uuid.uuid4()
    quantity = 2  # Remove all

    # Mock receipt with the product
    receipt = Receipt(
        shift_id=uuid.uuid4(),
        id=receipt_id,
        products=[
            ReceiptItem(
                product_id=product_id,
                quantity=2,
                unit_price=10.0,
            )
        ],
        subtotal=20.0,
        total=20.0,
    )
    mock_receipt_repository.get.return_value = receipt

    # Mock updated receipt after removal
    updated_receipt = Receipt(
        shift_id=receipt.shift_id,
        id=receipt_id,
        products=[],  # Empty after removal
        subtotal=0.0,
        total=0.0,
    )

    # Mock discount service
    mock_discount_service.apply_discounts.return_value = updated_receipt

    # Mock repository update
    mock_receipt_repository.update.return_value = updated_receipt

    # Act
    result = receipt_service.remove_product(receipt_id, product_id, quantity)

    # Assert
    assert result == updated_receipt
    assert len(result.products) == 0

    mock_receipt_repository.get.assert_called_once_with(receipt_id)
    mock_discount_service.apply_discounts.assert_called_once()
    mock_receipt_repository.update.assert_called_once_with(receipt_id, updated_receipt)


def test_remove_product_partial_removal(
    receipt_service: ReceiptService,
    mock_receipt_repository: Mock,
    mock_discount_service: Mock,
) -> None:
    """Test partially removing a product from a receipt."""
    # Arrange
    receipt_id = uuid.uuid4()
    product_id = uuid.uuid4()
    initial_quantity = 3
    remove_quantity = 2

    # Mock receipt with the product
    receipt = Receipt(
        shift_id=uuid.uuid4(),
        id=receipt_id,
        products=[
            ReceiptItem(
                product_id=product_id,
                quantity=initial_quantity,
                unit_price=10.0,
            )
        ],
        subtotal=30.0,
        total=30.0,
    )
    mock_receipt_repository.get.return_value = receipt

    # Mock updated receipt after partial removal
    updated_receipt = Receipt(
        shift_id=receipt.shift_id,
        id=receipt_id,
        products=[
            ReceiptItem(
                product_id=product_id,
                quantity=initial_quantity - remove_quantity,
                unit_price=10.0,
            )
        ],
        subtotal=10.0,
        total=10.0,
    )

    # Mock discount service
    mock_discount_service.apply_discounts.return_value = updated_receipt

    # Mock repository update
    mock_receipt_repository.update.return_value = updated_receipt

    # Act
    result = receipt_service.remove_product(receipt_id, product_id, remove_quantity)

    # Assert
    assert result == updated_receipt
    assert len(result.products) == 1
    assert result.products[0].quantity == initial_quantity - remove_quantity

    mock_receipt_repository.get.assert_called_once_with(receipt_id)
    mock_discount_service.apply_discounts.assert_called_once()
    mock_receipt_repository.update.assert_called_once_with(receipt_id, updated_receipt)


def test_remove_product_product_not_in_receipt(
    receipt_service: ReceiptService,
    mock_receipt_repository: Mock,
) -> None:
    """Test removing a product that isn't in the receipt."""
    # Arrange
    receipt_id = uuid.uuid4()
    product_id = uuid.uuid4()
    other_product_id = uuid.uuid4()
    quantity = 1

    # Mock receipt with a different product
    receipt = Receipt(
        shift_id=uuid.uuid4(),
        id=receipt_id,
        products=[
            ReceiptItem(
                product_id=other_product_id,
                quantity=2,
                unit_price=10.0,
            )
        ],
        subtotal=20.0,
        total=20.0,
    )
    mock_receipt_repository.get.return_value = receipt

    # Act
    result = receipt_service.remove_product(receipt_id, product_id, quantity)

    # Assert
    assert result == receipt  # Should return the unchanged receipt
    assert len(result.products) == 1
    assert result.products[0].product_id == other_product_id

    mock_receipt_repository.get.assert_called_once_with(receipt_id)


def test_calculate_payment_quote(
    receipt_service: ReceiptService,
    mock_receipt_repository: Mock,
    mock_exchange_service: Mock,
) -> None:
    """Test calculating a payment quote."""
    # Arrange
    receipt_id = uuid.uuid4()
    currency = Currency.USD

    # Mock receipt
    receipt = Receipt(
        shift_id=uuid.uuid4(),
        id=receipt_id,
        subtotal=100.0,
        total=100.0,
    )
    mock_receipt_repository.get.return_value = receipt

    # Mock quote
    expected_quote = Quote(
        receipt_id=receipt_id,
        base_currency=Currency.GEL,
        requested_currency=currency,
        exchange_rate=2.5,
        total_in_base_currency=100.0,
        total_in_requested_currency=40.0,  # 100.0 / 2.5
    )
    mock_exchange_service.calculate_quote.return_value = expected_quote

    # Act
    result = receipt_service.calculate_payment_quote(receipt_id, currency)

    # Assert
    assert result == expected_quote
    mock_receipt_repository.get.assert_called_once_with(receipt_id)
    mock_exchange_service.calculate_quote.assert_called_once_with(receipt, currency)


def test_calculate_payment_quote_receipt_not_found(
    receipt_service: ReceiptService,
    mock_receipt_repository: Mock,
) -> None:
    """Test calculating a payment quote for a non-existent receipt."""
    # Arrange
    receipt_id = uuid.uuid4()
    currency = Currency.USD

    # Mock receipt not found
    mock_receipt_repository.get.return_value = None

    # Act
    result = receipt_service.calculate_payment_quote(receipt_id, currency)

    # Assert
    assert result is None
    mock_receipt_repository.get.assert_called_once_with(receipt_id)


def test_add_payment_success(
    receipt_service: ReceiptService,
    mock_receipt_repository: Mock,
    mock_payment_repository: Mock,
    mock_exchange_service: Mock,
) -> None:
    """Test successfully adding a payment to a receipt."""
    # Arrange
    receipt_id = uuid.uuid4()
    amount = 100.0
    currency_name = "GEL"

    # Mock receipt before payment
    receipt = Receipt(
        shift_id=uuid.uuid4(),
        id=receipt_id,
        status=ReceiptStatus.OPEN,
        total=100.0,
    )
    mock_receipt_repository.get.return_value = receipt

    # Mock exchange rate
    mock_exchange_service.get_exchange_rate.return_value = 1.0  # 1:1 for GEL

    # Mock payment creation
    payment_id = uuid.uuid4()
    payment = Payment(
        id=payment_id,
        receipt_id=receipt_id,
        payment_amount=amount,
        currency=Currency.GEL,
        total_in_gel=100.0,
        exchange_rate=1.0,
        status=PaymentStatus.COMPLETED,
    )
    mock_payment_repository.create.return_value = payment

    # Mock updated receipt after payment
    updated_receipt = Receipt(
        shift_id=receipt.shift_id,
        id=receipt_id,
        status=ReceiptStatus.CLOSED,  # Closed because fully paid
        total=100.0,
        payments=[payment],
    )
    mock_receipt_repository.get.side_effect = [receipt, updated_receipt]
    mock_receipt_repository.update_status.return_value = updated_receipt

    # Act
    result = receipt_service.add_payment(receipt_id, amount, currency_name)

    # Assert
    assert result is not None
    payment_result, receipt_result = result

    assert receipt_result == updated_receipt
    assert receipt_result.status == ReceiptStatus.CLOSED

    mock_receipt_repository.get.assert_called_with(receipt_id)
    mock_exchange_service.get_exchange_rate.assert_called_with(
        Currency.GEL, Currency.GEL
    )
    mock_payment_repository.create.assert_called_once_with(
        receipt_id, amount, Currency.GEL, receipt.total, 1.0
    )


def test_add_payment_partial_payment(
    receipt_service: ReceiptService,
    mock_receipt_repository: Mock,
    mock_payment_repository: Mock,
    mock_exchange_service: Mock,
) -> None:
    """Test adding a partial payment (not enough to close the receipt)."""
    # Arrange
    receipt_id = uuid.uuid4()
    amount = 50.0  # Partial payment
    currency_name = "GEL"

    # Mock receipt before payment
    receipt = Receipt(
        shift_id=uuid.uuid4(),
        id=receipt_id,
        status=ReceiptStatus.OPEN,
        total=100.0,
    )
    mock_receipt_repository.get.return_value = receipt

    # Mock exchange rate
    mock_exchange_service.get_exchange_rate.return_value = 1.0  # 1:1 for GEL

    # Mock payment creation
    payment_id = uuid.uuid4()
    payment = Payment(
        id=payment_id,
        receipt_id=receipt_id,
        payment_amount=amount,
        currency=Currency.GEL,
        total_in_gel=50.0,
        exchange_rate=1.0,
        status=PaymentStatus.FAILED,
    )
    mock_payment_repository.create.return_value = payment

    # Mock updated receipt after payment (still open)
    updated_receipt = Receipt(
        shift_id=receipt.shift_id,
        id=receipt_id,
        status=ReceiptStatus.OPEN,  # Still open because not fully paid
        total=100.0,
        payments=[payment],
    )
    mock_receipt_repository.get.side_effect = [receipt, updated_receipt]

    # Act
    result = receipt_service.add_payment(receipt_id, amount, currency_name)

    # Assert
    assert result is not None
    payment_result, receipt_result = result

    assert receipt_result == updated_receipt
    assert receipt_result.status == ReceiptStatus.OPEN  # Still open

    mock_receipt_repository.get.assert_called_with(receipt_id)
    mock_exchange_service.get_exchange_rate.assert_called_with(
        Currency.GEL, Currency.GEL
    )
    mock_payment_repository.create.assert_called_once_with(
        receipt_id, amount, Currency.GEL, receipt.total, 1.0
    )
    # Status update not called because not fully paid
    mock_receipt_repository.update_status.assert_not_called()


def test_add_payment_receipt_not_found(
    receipt_service: ReceiptService,
    mock_receipt_repository: Mock,
) -> None:
    """Test adding a payment to a non-existent receipt."""
    # Arrange
    receipt_id = uuid.uuid4()
    amount = 100.0
    currency_name = "GEL"

    # Mock receipt not found
    mock_receipt_repository.get.return_value = None

    # Act
    result = receipt_service.add_payment(receipt_id, amount, currency_name)

    # Assert
    assert result is None
    mock_receipt_repository.get.assert_called_once()


def test_add_payment_closed_receipt(
    receipt_service: ReceiptService,
    mock_receipt_repository: Mock,
) -> None:
    """Test adding a payment to a closed receipt."""
    # Arrange
    receipt_id = uuid.uuid4()
    amount = 100.0
    currency_name = "GEL"

    # Mock closed receipt
    receipt = Receipt(
        shift_id=uuid.uuid4(),
        id=receipt_id,
        status=ReceiptStatus.CLOSED,
    )
    mock_receipt_repository.get.return_value = receipt

    # Act
    result = receipt_service.add_payment(receipt_id, amount, currency_name)

    # Assert
    assert result is None
    mock_receipt_repository.get.assert_called_once()


def test_add_payment_invalid_currency(
    receipt_service: ReceiptService,
    mock_receipt_repository: Mock,
) -> None:
    """Test adding a payment with invalid currency."""
    # Arrange
    receipt_id = uuid.uuid4()
    amount = 100.0
    currency_name = "INVALID"  # Invalid currency

    # Mock receipt
    receipt = Receipt(
        shift_id=uuid.uuid4(),
        id=receipt_id,
        status=ReceiptStatus.OPEN,
    )
    mock_receipt_repository.get.return_value = receipt

    # Act
    result = receipt_service.add_payment(receipt_id, amount, currency_name)

    # Assert
    assert result is None
    mock_receipt_repository.get.assert_called_once()


def test_get_receipts_by_shift(
    receipt_service: ReceiptService,
    mock_receipt_repository: Mock,
    mock_shift_repository: Mock,
) -> None:
    """Test getting all receipts for a shift."""
    # Arrange
    shift_id = uuid.uuid4()

    # Mock shift exists
    mock_shift_repository.get_by_id.return_value = {
        "id": shift_id,
        "status": ShiftStatus.OPEN,
    }

    # Mock receipts
    receipt_1 = Receipt(shift_id=shift_id, id=uuid.uuid4())
    receipt_2 = Receipt(shift_id=shift_id, id=uuid.uuid4())
    expected_receipts = [receipt_1, receipt_2]
    mock_receipt_repository.get_receipts_by_shift.return_value = expected_receipts

    # Act
    result = receipt_service.get_receipts_by_shift(shift_id, mock_shift_repository)

    # Assert
    assert result == expected_receipts
    mock_shift_repository.get_by_id.assert_called_once_with(shift_id)
    mock_receipt_repository.get_receipts_by_shift.assert_called_once_with(shift_id)


def test_get_receipts_by_shift_not_found(
    receipt_service: ReceiptService,
    mock_shift_repository: Mock,
) -> None:
    """Test getting receipts for a non-existent shift."""
    # Arrange
    shift_id = uuid.uuid4()

    # Mock shift doesn't exist
    mock_shift_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(ShiftNotFoundError) as exc_info:
        receipt_service.get_receipts_by_shift(shift_id, mock_shift_repository)

    assert str(shift_id) in str(exc_info.value)
    mock_shift_repository.get_by_id.assert_called_once_with(shift_id)
