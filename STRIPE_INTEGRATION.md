# Stripe Integration for GreenCart API

This document describes the Stripe payment integration implemented in the GreenCart API.

## Overview

The payments app provides a complete Stripe integration with the following features:

- **Payment Processing**: Create and manage payment intents
- **Refund Management**: Process full and partial refunds
- **Webhook Handling**: Automatic status updates from Stripe
- **Admin Interface**: Manage payments and refunds through Django admin
- **API Documentation**: Full OpenAPI/Swagger documentation

## Models

### Payment
- Stores payment information linked to orders
- Tracks Stripe PaymentIntent IDs and status
- Supports multiple payment methods (card, SEPA, etc.)
- Includes fee tracking and metadata storage

### Refund
- Manages refund requests and processing
- Links to parent payments
- Tracks refund reasons and status
- Supports partial refunds

### WebhookEvent
- Logs all incoming Stripe webhook events
- Tracks processing status for debugging
- Stores complete event data for audit trails

## API Endpoints

### Payments
- `GET /api/payments/payments/` - List payments
- `POST /api/payments/payments/` - Create payment intent
- `GET /api/payments/payments/{id}/` - Get payment details
- `POST /api/payments/payments/{id}/confirm/` - Confirm payment
- `POST /api/payments/payments/{id}/cancel/` - Cancel payment
- `GET /api/payments/payments/stats/` - Payment statistics (admin)

### Refunds
- `GET /api/payments/refunds/` - List refunds
- `POST /api/payments/refunds/` - Create refund
- `GET /api/payments/refunds/{id}/` - Get refund details

### Configuration
- `GET /api/payments/config/` - Get Stripe public configuration

### Webhooks
- `POST /api/payments/webhooks/stripe/` - Stripe webhook endpoint
- `GET /api/payments/webhooks/test/` - Test webhook accessibility

## Environment Variables

Set these environment variables for Stripe integration:

\`\`\`bash
# Required
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Optional
STRIPE_CURRENCY=EUR
STRIPE_AUTOMATIC_TAX=False
PAYMENT_SUCCESS_URL=http://localhost:3000/payment/success
PAYMENT_CANCEL_URL=http://localhost:3000/payment/cancel
\`\`\`

## Webhook Configuration

Configure your Stripe webhook endpoint with these settings:

**Endpoint URL**: `https://yourdomain.com/api/payments/webhooks/stripe/`

**Events to listen for**:
- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `payment_intent.canceled`
- `payment_intent.processing`
- `payment_intent.requires_action`
- `charge.dispute.created`
- `refund.created`
- `refund.updated`

## Usage Example

### Creating a Payment

```python
# 1. Create payment intent
POST /api/payments/payments/
{
    "order_id": "uuid-of-order",
    "return_url": "https://myapp.com/payment/return"
}

# Response
{
    "payment_id": "uuid-of-payment",
    "client_secret": "pi_xxx_secret_xxx",
    "publishable_key": "pk_test_xxx",
    "amount": "25.50",
    "currency": "EUR"
}

# 2. Use client_secret in frontend with Stripe.js
# 3. Confirm payment on frontend
# 4. Webhook automatically updates payment status
