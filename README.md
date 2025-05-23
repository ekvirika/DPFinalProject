# POS System API Documentation

This document outlines the API for a Point of Sales (POS) system, detailing the endpoints, request formats, and response structures.

***Please run this in terminal:***  
```bash
mypy --install-types 
```
## Table of Contents
- [Products Management](#products)
- [Campaign Management](#campaigns)
- [Shift Management](#shifts)
- [Receipt Management](#receipts)
- [Reporting](#reporting)
- [Payment](#payment)

## Products

### Create Product

**`POST /products`**

Creates a new product in the system.

**Request Body**:
```json
{
  "name": "Milk",
  "price": 3.99
}
```

**Response** (201 Created):
```json
{
  "product": {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "Milk",
    "price": 3.99
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "detail": "Invalid product data. Price must be greater than 0."
}
```

### List Products

**`GET /products`**

Retrieves a list of all products.

**Response** (200 OK):
```json
{
  "products": [
    {
      "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "name": "Milk",
      "price": 3.99
    },
    {
      "id": "f47ac10b-58cc-4372-a567-0e02b2c3d480",
      "name": "Bread",
      "price": 2.50
    }
    // ... other products
  ]
}
```

### Update Product

**`PATCH /products/{product_id}`**

Updates an existing product's price.

**URL Parameters**:
- `product_id`: UUID of the product to update

**Request Body**:
```json
{
  "price": 4.25
}
```

**Response** (200 OK):
```json
{
  "product": {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "Milk",
    "price": 4.25
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "detail": "Product with ID 'f47ac10b-58cc-4372-a567-0e02b2c3d479' not found"
}
```

## Campaigns

### Create Campaign

**`POST /campaigns`**

Creates a new campaign.

#### Discount Campaign for Product

**Request Body**:
```json
{
  "name": "Summer Sale",
  "campaign_type": "discount",
  "rules": {
    "discount_value": 10,
    "applies_to": "product",
    "product_ids": [
      "3fa85f64-5717-4562-b3fc-2c963f66afa6", 
      "4fa85f64-5717-4562-b3fc-2c963f66afa7"
    ]
  }
}
```

**Response** (201 Created):
```json
{
  "campaign": {
    "id": "a41c6b3e-7a91-4d1f-8c25-9863d3f9c0c5",
    "name": "Summer Sale",
    "campaign_type": "discount",
    "rules": {
      "discount_value": 10,
      "applies_to": "product",
      "product_ids": [
        "3fa85f64-5717-4562-b3fc-2c963f66afa6", 
        "4fa85f64-5717-4562-b3fc-2c963f66afa7"
      ]
    }
  }
}
```

#### Discount Campaign for Receipt

**Request Body**:
```json
{
  "name": "Spring Sale",
  "campaign_type": "discount",
  "rules": {
    "discount_value": 10,
    "applies_to": "receipt",
    "min_amount": 100
  }
}
```

**Response** (201 Created):
```json
{
  "campaign": {
    "id": "a41c6b3e-7a91-4d1f-8c25-9863d3f9c0c5",
    "name": "Spring Sale",
    "campaign_type": "discount",
    "rules": {
      "discount_value": 10,
      "applies_to": "receipt",
      "min_amount": 100
    }
  }
}
```

#### Buy N Get N Campaign

**Request Body**:
```json
{
  "name": "Buy 2 Get 1 Free",
  "campaign_type": "buy_n_get_n",
  "rules": {
    "buy_product_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "buy_quantity": 2,
    "get_product_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "get_quantity": 1
  }
}
```

**Response** (201 Created):
```json
{
  "campaign": {
    "id": "a41c6b3e-7a91-4d1f-8c25-9863d3f9c0c5",
    "name": "Buy 2 Get 1 Free",
    "campaign_type": "buy_n_get_n",
    "rules": {
      "buy_product_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "buy_quantity": 2,
      "get_product_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "get_quantity": 1
    }
  }
}
```

#### Combo Campaign

**Request Body**:
```json
{
  "name": "Breakfast Combo",
  "campaign_type": "combo",
  "rules": {
    "product_ids": [
      "3fa85f64-5717-4562-b3fc-2c963f66afa6", 
      "4fa85f64-5717-4562-b3fc-2c963f66afa7"
    ],
    "discount_type": "percentage",
    "discount_value": 15
  }
}
```

**Response** (201 Created):
```json
{
  "campaign": {
    "id": "a41c6b3e-7a91-4d1f-8c25-9863d3f9c0c5",
    "name": "Breakfast Combo",
    "campaign_type": "combo",
    "rules": {
      "product_ids": [
        "3fa85f64-5717-4562-b3fc-2c963f66afa6", 
        "4fa85f64-5717-4562-b3fc-2c963f66afa7"
      ],
      "discount_type": "percentage",
      "discount_value": 15
    }
  }
}
```

**Error Responses** (400 Bad Request):

For discount campaign:
```json
{
  "detail": "Invalid campaign data. Discount percentage must be between 1 and 100."
}
```

For buy-n-get-n campaign:
```json
{
  "detail": "Invalid campaign data. Buy quantity must be greater than 0."
}
```

For combo campaign:
```json
{
  "detail": "Invalid campaign data. At least 2 products are required for a combo campaign."
}
```

For all campaign types:
```json
{
  "detail": "Invalid campaign data. End date must be after start date."
}
```

For product validation:
```json
{
  "detail": "One or more product IDs do not exist in the system."
}
```

### Deactivate Campaign

**`DELETE /campaigns/{campaign_id}`**

Deactivates an existing campaign.

**URL Parameters**:
- `campaign_id`: UUID of the campaign to deactivate

**Response** (200 OK)

**Error Response** (404 Not Found):
```json
{
  "detail": "Campaign with ID 'a41c6b3e-7a91-4d1f-8c25-9863d3f9c0c5' not found"
}
```

### List Campaigns

**`GET /campaigns`**

Retrieves a list of all campaigns.

**Response** (200 OK):
```json
{
  "campaigns": [
    {
      "id": "a41c6b3e-7a91-4d1f-8c25-9863d3f9c0c5",
      "name": "Breakfast Combo",
      "campaign_type": "combo",
      "rules": {
        "product_ids": [
          "3fa85f64-5717-4562-b3fc-2c963f66afa6", 
          "4fa85f64-5717-4562-b3fc-2c963f66afa7"
        ],
        "discount_type": "percentage",
        "discount_value": 15
      }
    },
    {
      "id": "a41c6b3e-7a91-4d1f-8c25-9863d3f9c0c5",
      "name": "Buy 2 Get 1 Free",
      "campaign_type": "buy_n_get_n",
      "rules": {
        "buy_product_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "buy_quantity": 2,
        "get_product_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "get_quantity": 1
      }
    }
    // ... other campaigns
  ]
}
```

### Get Campaign by ID

**`GET /campaigns/{campaign_id}`**

Retrieves a specific campaign by ID.

**URL Parameters**:
- `campaign_id`: UUID of the campaign

**Response** (200 OK):
```json
{
  "campaign": {
    "id": "5fa85f64-5717-4562-b3fc-2c963f66afa8",
    "name": "Summer Sale",
    "campaign_type": "discount",
    "rules": {
      "discount_value": 10,
      "applies_to": "product",
      "product_ids": [
        "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "3fa85f64-7777-4562-b3fc-2c963f66afa6"
      ]
    }
  }
}
```

## Shifts

### Open Shift

**`POST /shifts`**

Opens a new cashier shift.

**Request Body**:
```json
{}
```

**Response** (201 Created):
```json
{
  "shift": {
    "id": "e09c6b3e-7a91-4d1f-8c25-9863d3f9c0a7",
    "status": "open"
  }
}
```

### Close Shift

**`PATCH /shifts/{shift_id}`**

Closes an open shift.

**URL Parameters**:
- `shift_id`: UUID of the shift to close

**Request Body**:
```json
{
  "status": "closed"
}
```

**Response** (200 OK):
```json
{
  "id": "e09c6b3e-7a91-4d1f-8c25-9863d3f9c0a7",
  "status": "closed",
  "receipt_count": 25,
  "items_sold": [
    {
      "product_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "name": "Milk",
      "quantity": 48
    },
    {
      "product_id": "f47ac10b-58cc-4372-a567-0e02b2c3d480",
      "name": "Bread",
      "quantity": 35
    }
    // ... other items
  ],
  "revenue_by_currency": [
    {
      "currency": "GEL",
      "amount": 650.75
    },
    {
      "currency": "USD",
      "amount": 89.25
    },
    {
      "currency": "EUR",
      "amount": 45.00
    }
  ]
}
```

## Receipts

### Create Receipt

**`POST /receipts`**

Creates a new receipt.

**Request Body**:
```json
{
  "shift_id": "e09c6b3e-7a91-4d1f-8c25-9863d3f9c0a7"
}
```

**Response** (201 Created):
```json
{
  "receipt": {
    "id": "c47ac10b-58cc-4372-a567-0e02b2c3d111",
    "shift_id": "e09c6b3e-7a91-4d1f-8c25-9863d3f9c0a7",
    "status": "open",
    "products": [],
    "subtotal": 0,
    "discount": 0,
    "total": 0
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "detail": "Shift with ID 'e09c6b3e-7a91-4d1f-8c25-9863d3f9c0a7' not found"
}
```

**Error Response** (400 Bad Request):
```json
{
  "detail": "Cannot create receipt for a closed shift"
}
```

### Add Item to Receipt

**`POST /receipts/{receipt_id}/products`**

Adds a product to an open receipt.

**URL Parameters**:
- `receipt_id`: UUID of the receipt

**Request Body**:
```json
{
  "product_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "quantity": 2
}
```

**Response** (200 OK):
```json
{
  "receipt": {
    "id": "7fa85f64-5717-4562-b3fc-2c963f66afaa",
    "shift_id": "6fa85f64-5717-4562-b3fc-2c963f66afa9",
    "status": "open",
    "products": [
      {
        "product_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "quantity": 2,
        "unit_price": 5.99,
        "total_price": 11.98,
        "discounts": [
          {
            "campaign_id": "5fa85f64-5717-4562-b3fc-2c963f66afa8",
            "campaign_name": "Summer Sale",
            "discount_amount": 1.20
          }
        ],
        "final_price": 10.78
      },
      {
        "product_id": "44a85f64-5717-4562-b3fc-2c963f66afa6",
        "quantity": 2,
        "unit_price": 4,
        "total_price": 8,
        "discounts": [],
        "final_price": 8
      }
    ],
    "subtotal": 19.98,
    "discount_amount": 1.20,
    "total": 18.78
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "detail": "Cannot add items to a closed receipt"
}
```

**Error Response** (404 Not Found):
```json
{
  "detail": "Product with ID 'f47ac10b-58cc-4372-a567-0e02b2c3d479' not found"
}
```

### Calculate Payment Quote

**`POST /receipts/{receipt_id}/quotes`**

Calculates the payment amount in a specific currency.

**URL Parameters**:
- `receipt_id`: UUID of the receipt

**Request Body**:
```json
{
  "currency": "USD" // GEL, USD, or EUR
}
```

**Response** (200 OK):
```json
{
  "quote": {
    "receipt_id": "7fa85f64-5717-4562-b3fc-2c963f66afaa",
    "base_currency": "GEL",
    "requested_currency": "USD",
    "exchange_rate": 0.37,
    "total_in_base_currency": 10.78,
    "total_in_requested_currency": 3.99
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "detail": "Unsupported currency. Supported currencies are: GEL, USD, EUR"
}
```

### Add Payment to Receipt

**`POST /receipts/{receipt_id}/payments`**

Records payment for a receipt and closes it if fully paid.

**URL Parameters**:
- `receipt_id`: UUID of the receipt

**Request Body**:
```json
{
  "amount": 5.73,
  "currency": "USD"
}
```

**Response** (200 OK):
```json
{
  "payment": {
    "id": "c47ac10b-58cc-4372-a567-0e02b2c3d111",
    "receipt_id": "7fa85f64-5717-4562-b3fc-2c963f66afaa",
    "total_in_gel": 15.07,
    "payment_amount": 5.73,
    "payment_currency": "USD",
    "paid_amount": 5.73,
    "status": "completed"
  },
  "receipt": {
    "id": "7fa85f64-5717-4562-b3fc-2c963f66afaa",
    "status": "closed"
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "detail": "Cannot add payment to a closed receipt"
}
```

### Get Receipt

**`GET /receipts/{receipt_id}`**

Retrieves a specific receipt.

**URL Parameters**:
- `receipt_id`: UUID of the receipt

**Response** (200 OK):
```json
{
  "receipt": {
    "id": "c47ac10b-58cc-4372-a567-0e02b2c3d111",
    "shift_id": "e09c6b3e-7a91-4d1f-8c25-9863d3f9c0a7",
    "products": [
      {
        "product_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "quantity": 2,
        "unit_price": 5.99,
        "total_price": 11.98,
        "discounts": [
          {
            "campaign_id": "5fa85f64-5717-4562-b3fc-2c963f66afa8",
            "campaign_name": "Summer Sale",
            "discount_amount": 1.20
          }
        ],
        "final_price": 10.78
      }       
    ],
    "subtotal": 11.98,
    "discount_amount": 1.20, 
    "total": 10.78,
    "payments": [
      {
        "payment_id": "e5f6a7b8-9c0d-1e2f-3a4b-5c6d7e8f9a0b",
        "payment_amount": 5.56,
        "currency": "USD",
        "total_in_gel": 10.78,
        "exchange_rate": 0.37,
        "status": "completed"
      }
    ],
    "status": "closed"
  }
}
```

## Reports

### X-Report (Shift State Report)

**`GET /x-reports`**

Generates an X-report for the current state of an open shift.

**Query Parameters**:
- `shift_id`: UUID of the shift

**Response** (200 OK):
```json
{
  "x-report": {
    "shift_id": "e09c6b3e-7a91-4d1f-8c25-9863d3f9c0a7",
    "receipt_count": 25,
    "items_sold": [
      {
        "product_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "name": "Milk",
        "quantity": 48
      },
      {
        "product_id": "f47ac10b-58cc-4372-a567-0e02b2c3d480",
        "name": "Bread",
        "quantity": 35
      }
      // ... other items
    ],
    "revenue_by_currency": [
      {
        "currency": "GEL",
        "amount": 650.75
      },
      {
        "currency": "USD",
        "amount": 89.25
      },
      {
        "currency": "EUR",
        "amount": 45.00
      }
    ]
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "detail": "Shift with ID 'e09c6b3e-7a91-4d1f-8c25-9863d3f9c0a7' not found"
}
```

### Sales Report (Lifetime)

**`GET /sales`**

Generates a lifetime sales report.

**Response** (200 OK):
```json
{
  "sales": {
    "total_items_sold": 5632,
    "total_receipts": 1500,
    "total_revenue": {
      "GEL": 25000.50,
      "USD": 3500.75,
      "EUR": 2800.30
    },
    "total_revenue_gel": 46800.25
  }
}
```

## Error Responses

All endpoints may return the following error responses:

**400 Bad Request**:
```json
{
  "detail": "Invalid request data. Please check your input."
}
```

**404 Not Found**:
```json
{
  "detail": "Resource not found."
}
```

**500 Internal Server Error**:
```json
{
  "detail": "An unexpected error occurred. Please try again later."
}
```
