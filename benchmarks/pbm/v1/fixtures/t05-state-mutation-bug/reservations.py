from __future__ import annotations


def reserve(stock: dict[str, int], sku: str, quantity: int) -> int:
    key = sku.upper()
    stock[key] -= quantity
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    if stock[key] < 0:
        raise ValueError("insufficient stock")
    return stock[key]
