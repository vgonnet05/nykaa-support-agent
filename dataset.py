import random
from collections import Counter

random.seed(50)  # Set the seed for reproducibility

CATEGORIES = [ "Apparel",
    "Electronics",
    "Home",
    "Footwear",
    "Beauty"]

STATUSES = [
    "Placed",
    "Shipped",
    "Delivered",
    "Returned",
    "Refunded"
]

# Create 50 category entries with equal representation:
# 10 orders per category.
category_list = CATEGORIES * 10 
random.shuffle(category_list)

# Create 50 status entries with a predefined distribution.
# Delivered orders have the highest representation.
status_list = (["Placed"] * 5
    + ["Shipped"] * 10
    + ["Delivered"] * 20
    + ["Returned"] * 7
    + ["Refunded"] * 8
)
random.shuffle(status_list)

# I set exactly 10 orders as delayed to guarantee a 20% rate.
delayed_list = [True] * 10 + [False] * 40
random.shuffle(delayed_list)

# Initialize an empty list to store all generated orders.
ORDERS = []

# Generate 50 orders, one dictionary per order.
for i in range(50):
    order = {
        # Generate a unique, sequential ID for each order.
        "record_id": f"ORD{1001 + i}",

        # Use the shuffled list to guarantee 10 orders per category.
        "category": category_list[i],

        # Use the shuffled list to maintain my predefined status distribution.
        "status": status_list[i],

        # Generate a random order value between ₹100 and ₹10,000.
        "order_value_inr": random.randint(100, 10000),

        # Generate an order age between 0 and 30 days.
        "days_since_created": random.randint(0, 30),

        # Randomly assign True or False.
        # I will refine this logic to meet the required delayed-shipment percentage.
        "delayed_shipment": random.choice([True, False])
    }

    # Add the generated order dictionary to the ORDERS list.
    ORDERS.append(order)

# Print the total number of generated orders.
print("Total orders generated:", len(ORDERS))

print("First order:", ORDERS[0])    

# Count how many orders belong to each category.
category_counts = Counter(order["category"] for order in ORDERS)

print("Category distribution:", category_counts)

# Count how many orders belong to each status.
status_counts = Counter(order["status"] for order in ORDERS)

print("Status distribution:", status_counts)