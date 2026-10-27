from pathlib import Path

# Define the folder where I store my knowledge-base documents.
folder = Path("knowledge_base")

# Define the content of my 10 remaining documents.
documents = {
    "cancellation_policy.txt": """Nykaa Cancellation Policy

Customers may request cancellation before an order is dispatched.
Cancellation availability depends on the current order status.
Orders that have already shipped may require a return request instead.""",

    "refund_policy.txt": """Nykaa Refund Policy

Refund eligibility depends on the order status and applicable product policy.
Approved refunds are processed through the applicable payment method or refund process.
The time required for a refund to appear may vary by payment provider.""",

    "payment_policy.txt": """Nykaa Payment Policy

Customers can use the payment methods available at checkout.
A payment may fail because of bank restrictions, insufficient funds, or a technical issue.
Customers should verify their payment status before attempting another payment.""",

    "order_tracking.txt": """Nykaa Order Tracking

Customers can check order progress using their order details.
Tracking information becomes available when the relevant shipment information is updated.
Tracking updates may take time to appear after an order is dispatched.""",

    "delivery_policy.txt": """Nykaa Delivery Policy

Delivery timelines depend on the delivery address, product availability, and courier service.
Customers should ensure their address and contact details are correct.
If delivery is delayed, customers should check their tracking information for updates.""",

    "damaged_product_policy.txt": """Nykaa Damaged Product Policy

Customers who receive a damaged product should report the issue through customer support.
They may be asked to provide photographs and order details for verification.
Resolution depends on the product, the evidence provided, and the applicable policy.""",

    "exchange_policy.txt": """Nykaa Exchange Policy

Exchange eligibility depends on the product category and applicable policy.
Customers should check whether their item qualifies before requesting an exchange.
Some products may require a return and a separate replacement order instead.""",

    "beauty_product_policy.txt": """Nykaa Beauty Product Policy

Beauty products should be checked for their product-specific usage and storage instructions.
Opened or used products may have different return eligibility because of hygiene considerations.
Customers should review the applicable policy before requesting a return.""",

    "warranty_policy.txt": """Nykaa Warranty Policy

Warranty coverage depends on the product and the manufacturer's terms.
Customers should retain their purchase details and any warranty documentation.
Warranty claims may require proof of purchase and an assessment of the reported issue.""",

    "escalation_policy.txt": """Nykaa Support Escalation Policy

Issues that cannot be resolved using available order information or documented policies should be escalated.
Suspected payment problems, repeated delivery failures, and unresolved complaints may require human support.
The support agent should explain the reason for escalation and avoid promising an unconfirmed outcome."""
}

# Create the folder if it does not already exist.
folder.mkdir(parents=True, exist_ok=True)

# Create each document inside the knowledge-base folder.
for filename, content in documents.items():
    (folder / filename).write_text(content, encoding="utf-8")

print(f"Created {len(documents)} knowledge-base documents.")