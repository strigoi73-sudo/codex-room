from __future__ import annotations


def reserve(stock: dict[str, int], sku: str, quantity: int) -> int:
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise ValueError("quantity must be a positive integer")

    matched_key = next(
        (key for key in stock if key.casefold() == sku.casefold()),
        None,
    )
    if matched_key is None:
        raise KeyError(sku)

    available = stock[matched_key]
    if available < quantity:
        raise ValueError("insufficient stock")

    remaining = available - quantity
    stock[matched_key] = remaining
    return remaining
