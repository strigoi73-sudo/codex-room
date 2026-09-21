from __future__ import annotations


def reserve_inventory(inventory: dict[str, int], requests) -> dict[str, int]:
    for row in requests:
        sku = row["sku"]
        quantity = row["quantity"]
        if sku not in inventory or inventory[sku] < quantity:
            raise ValueError("insufficient inventory")
        inventory[sku] -= quantity
    return inventory
