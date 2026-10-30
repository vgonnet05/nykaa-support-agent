import json

from dataset import ORDERS


def check_order_status(record_id: str) -> dict:
    """
    Find an order by its ID and calculate its escalation score.

    Args:
        record_id: The unique ID of the order, e.g. ORD1001.

    Returns:
        A dictionary containing order details and escalation score,
        or an error if the order does not exist.
    """

    # Step 1: Search for the order matching the supplied record ID.
    # next() returns the first matching order.
    # If no order matches, it returns None.
    order = next(
        (item for item in ORDERS if item["record_id"] == record_id),
        None,
    )

    # Step 2: Handle the case where the order ID was not found.
    if order is None:
        return {"error": "Order not found"}

    # Step 3: Normalize the order age to a value between 0 and 1.
    # The dataset uses an order age between 0 and 30 days.
    normalized_recency = order["days_since_created"] / 30

    # Step 4: Convert the delayed-shipment flag into a numeric value.
    # True becomes 1.0; False becomes 0.0.
    delayed_factor = 1.0 if order["delayed_shipment"] else 0.0

    # Step 5: Calculate the escalation score.
    # Delayed shipment contributes 60%; order age contributes 40%.
    escalation_score = (
        0.6 * delayed_factor
        + 0.4 * normalized_recency
    )

    # Step 6: Return only the required order information.
    # round() limits the score to two decimal places.
    return {
        "record_id": order["record_id"],
        "status": order["status"],
        "order_value_inr": order["order_value_inr"],
        "escalation_score": round(escalation_score, 2),
    }


if __name__ == "__main__":
    # This block runs only when this file is executed directly.
    # It demonstrates both a successful lookup and a missing order.
    print("Existing order:")
    print(json.dumps(check_order_status("ORD1001"), indent=2))

    print("\nNon-existing order:")
    print(json.dumps(check_order_status("ORD9999"), indent=2))