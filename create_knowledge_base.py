from pathlib import Path

# Generates the 10 automated policy documents for the Nykaa capstone.
# Numerical timelines below are fictional project assumptions, not
# verified official Nykaa policies. The two manually maintained files
# (return_policy.txt and shipping_policy.txt) are intentionally untouched.

folder = Path("knowledge_base")

documents = {
    "cancellation_policy.txt": """Nykaa Cancellation Policy — Project Assumptions

Customers may request cancellation before an order is dispatched, subject to the current order status. Once an order has shipped, the customer may need to request a return instead. Cancellation availability must be checked against the order record before a promise is made. These conditions are project assumptions and are not verified official Nykaa policies.""",

    "refund_policy.txt": """Nykaa Refund Policy — Project Assumptions

For this project, approved refunds are assumed to reach the customer's account within 5–7 business days, depending on the payment provider and method. For cash-on-delivery (COD) orders, valid refund-account details must be provided before processing can proceed. Refund eligibility depends on order status and the applicable product policy. These timelines and conditions are fictional project assumptions, not verified official Nykaa policies.""",

    "payment_policy.txt": """Nykaa Payment Policy — Project Assumptions

Customers can use the payment methods offered at checkout, and a payment may fail because of bank restrictions, insufficient funds, or technical issues. Customers should verify the transaction status before retrying to reduce the risk of duplicate payments. A retry should be attempted only when the payment provider or transaction status indicates that it is appropriate. Loyalty-point redemption requires an eligible account, available points, and a qualifying purchase. These rules are project assumptions and are not verified official Nykaa policies.""",

    "international_shipping_policy.txt": """Nykaa International Shipping Policy — Project Assumptions

International shipping availability depends on the destination country and applicable product restrictions. For this project, international delivery is treated as unavailable unless the destination is explicitly listed as supported in the configured policy. Customers should confirm destination eligibility, product eligibility, and shipping charges before placing an order. This rule is a project assumption, not a verified official Nykaa policy.""",

    "delivery_policy.txt": """Nykaa Delivery Policy — Project Assumptions

For this project, the estimated delivery SLA is 2–4 business days for metro areas and 4–7 business days for other serviceable areas, starting after dispatch. Timelines may vary with product availability, destination, and courier operations, so the order's tracking information should be checked. If delivery is more than 2 business days beyond the applicable estimate, the case should be escalated if tracking does not resolve the issue. These SLAs are fictional project assumptions, not verified official Nykaa policies.""",

    "damaged_product_policy.txt": """Nykaa Damaged Product Policy — Project Assumptions

Customers who receive a damaged or defective product should report the issue to customer support within 48 hours of delivery for this project. They should provide the order details and clear photographs when requested so the claim can be assessed. Resolution may involve a return, replacement, or refund depending on eligibility and verification. The 48-hour reporting period is a fictional project assumption, not a verified official Nykaa policy.""",

    "exchange_policy.txt": """Nykaa Exchange Policy — Project Assumptions

For this project, size exchanges may be requested for eligible Apparel and Footwear products within 7 days of delivery, subject to replacement-size availability. Electronics, Home, and Beauty products are not assumed to qualify for size exchange; their eligibility must be checked against the applicable product policy. Some cases may require a return followed by a separate replacement order. These conditions are fictional project assumptions, not verified official Nykaa policies.""",

    "loyalty_points_policy.txt": """Nykaa Loyalty Points Redemption Policy — Project Assumptions

Customers may redeem loyalty points only when their account and purchase meet the configured redemption conditions. For this project, points can cover up to 10% of an eligible order value, provided the account has enough available points. Available balance and eligibility must be checked before points are applied, and points cannot be promised as redeemable without that check. The 10% limit is a fictional project assumption, not a verified official Nykaa policy.""",

    "warranty_policy.txt": """Nykaa Warranty Policy — Project Assumptions

For this project, eligible Electronics products are assumed to have a 12-month warranty, while eligible Home appliances are assumed to have a 6-month warranty, subject to manufacturer terms and proof of purchase. Apparel, Footwear, and Beauty products have no additional project-assumed warranty unless the product listing or manufacturer documentation explicitly states otherwise. Warranty coverage starts from the purchase date and excludes issues not covered by the applicable manufacturer terms. These periods are fictional project assumptions, not verified official Nykaa policies.""",

    "escalation_policy.txt": """Nykaa Support Escalation Policy — Project Assumptions

Level 1 handles routine policy questions and order-status requests using the knowledge base and verified order information. Level 2 handles unresolved delivery delays, return or refund disputes, and exchange-eligibility questions. Level 3 handles suspected payment discrepancies, possible duplicate charges, suspected fraud, and unresolved complaints requiring specialist review. The agent must explain why escalation is needed and must not promise an unconfirmed outcome. This escalation matrix is a project assumption, not a verified official Nykaa policy.""",
}

folder.mkdir(parents=True, exist_ok=True)

for filename, text in documents.items():
    (folder / filename).write_text(text.strip() + "\n", encoding="utf-8")

print(f"Created/updated {len(documents)} knowledge-base documents.")
print("Manual documents left untouched: return_policy.txt, shipping_policy.txt")
print("Reminder: numerical policy values are fictional project assumptions.")
