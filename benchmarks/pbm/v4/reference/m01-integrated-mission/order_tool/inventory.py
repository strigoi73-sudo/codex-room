from __future__ import annotations


def _validate_inventory(inventory: dict[str, int]) -> None:
    if not isinstance(inventory, dict):
        raise ValueError("inventory must be a dictionary")
    for sku, quantity in inventory.items():
        if not isinstance(sku, str) or not sku:
            raise ValueError("inventory sku must be a non-empty string")
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 0:
            raise ValueError("inventory quantity must be a non-negative integer")


def reserve_inventory(inventory: dict[str, int], requests) -> dict[str, int]:
    _validate_inventory(inventory)
    demand: dict[str, int] = {}
    try:
        rows = list(requests)
    except TypeError as exc:
        raise ValueError("requests must be iterable") from exc
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("reservation row must be a dictionary")
        sku = row.get("sku")
        quantity = row.get("quantity")
        if not isinstance(sku, str) or not sku:
            raise ValueError("reservation sku must be a non-empty string")
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("reservation quantity must be a positive integer")
        if sku not in inventory:
            raise ValueError("reservation sku is not present in inventory")
        demand[sku] = demand.get(sku, 0) + quantity
    for sku, quantity in demand.items():
        if inventory[sku] < quantity:
            raise ValueError("insufficient inventory")
    for sku, quantity in demand.items():
        inventory[sku] -= quantity
    return inventory
