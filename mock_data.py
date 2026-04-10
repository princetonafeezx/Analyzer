def generate_mock_transactions() -> list[CategorizedRecord]:
    """Build six months of repeatable categorized mock transactions."""
    records: list[CategorizedRecord] = []  # Initialize the list to store the generated records
    template = [  # Define a list of recurring transactions to be used as a base each month
        (1, "Landlord Portal", 1450.00),  # Fixed monthly rent payment
        (3, "Comcast Cable", 82.00),      # Standard monthly internet/cable bill
        (5, "Whole Foods", 118.24),       # Grocery shopping trip
        (7, "Netflix", 15.49),            # Digital streaming subscription
        (8, "Spotify", 9.99),             # Music subscription service
        (10, "Shell", 54.12),             # Fuel or gas station expense
        (12, "Amazon Marketplace", 64.70),# General retail/shopping purchase
        (14, "PGE Utilities", 91.34),     # Monthly utility bill
        (17, "Starbucks", 7.45),          # Coffee shop purchase
        (20, "Trader Joes", 96.55),       # Secondary grocery trip
        (22, "Uber Trip", 19.40),         # Transportation or ride-share cost
        (24, "Walgreens", 22.18),         # Pharmacy or health-related spend
        (26, "Starbucks", 6.95),          # Second coffee shop visit of the month
    ]

    for offset in range(5, -1, -1):  # Iterate backwards from 5 months ago to the current month (0)
        year, month = month_start_from_offset(offset)  # Calculate the specific year and month for the offset
        for day_number, merchant, amount in template:  # Loop through each item in the monthly template
            payload = rule_payload_from_merchant(merchant)  # Determine category/subcategory based on merchant name
            adjusted_amount = amount + ((month % 3) * 1.15)  # Add minor monthly variance to prevent identical amounts
            entry = cast(  # Create the record dictionary and cast to the CategorizedRecord type
                CategorizedRecord,
                {
                    "date": date(year, month, min(day_number, 28)),  # Ensure day is valid for all months (caps at 28)
                    "merchant": merchant,  # Set the merchant name from the template
                    "amount": round(adjusted_amount, 2),  # Round the varied amount to standard currency precision
                    "category": payload["category"],  # Assign the detected primary category
                    "subcategory": payload["subcategory"],  # Assign the detected subcategory
                },
            )
            records.append(entry)  # Add the generated monthly entry to the main record list

        if offset == 2:  # Inject a specific high-value anomaly two months ago
            records.append(
                cast(
                    CategorizedRecord,
                    {
                        "date": date(year, month, 12),  # Set specific date for the anomaly
                        "merchant": "Amazon Marketplace",  # Re-use known merchant name
                        "amount": 420.00,  # Large amount designed to trigger the 3x average detector
                        "category": "Shopping",  # Explicitly set the category
                        "subcategory": "Shopping",  # Explicitly set the subcategory
                    },
                )
            )

        if offset == 1:  # Inject duplicate records one month ago to test deduplication logic
            duplicate = cast(
                CategorizedRecord,
                {
                    "date": date(year, month, 17),  # Matches the Starbucks entry in the template
                    "merchant": "Starbucks",  # Matches the Starbucks entry in the template
                    "amount": 7.45,  # Matches the original amount exactly
                    "category": "Food & Drink",  # Standard categorization for coffee
                    "subcategory": "Dining Out",  # Standard sub-categorization
                },
            )
            records.append(duplicate.copy())  # Append the first duplicate instance
            records.append(duplicate.copy())  # Append the second duplicate instance

    return records  # Return the full list of mock transactions for analysis