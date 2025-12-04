from collections import defaultdict

def calculate_settlement(expense_rows):
    """
    expense_rows: list of tuples (payer_id, amount)
    Returns: {payer_id: balance}
    Positive balance = person paid more than their share
    Negative balance = person owes money
    """
    totals = defaultdict(float)

    # Sum how much each person paid
    for payer, amount in expense_rows:
        totals[int(payer)] += float(amount)

    people = list(totals.keys())
    if not people:
        return {}

    total_amount = sum(totals.values())
    per_person_share = total_amount / len(people)

    # Calculate how much each person owes or is owed
    balances = {p: round(totals[p] - per_person_share, 2) for p in people}

    return balances
