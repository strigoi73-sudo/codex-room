from __future__ import annotations

import copy
import unittest

from order_tool.codec import decode, encode
from order_tool.inventory import reserve_inventory
from order_tool.report import summarize_orders


class PublicTests(unittest.TestCase):
    def test_codec_basic_roundtrip(self):
        fields = ["alpha", "b|eta", r"c\d", ""]
        self.assertEqual(decode(encode(fields)), fields)

    def test_inventory_success(self):
        inventory = {"a": 5, "b": 2}
        result = reserve_inventory(
            inventory,
            [{"sku": "a", "quantity": 2}, {"sku": "b", "quantity": 1}],
        )
        self.assertIs(result, inventory)
        self.assertEqual(inventory, {"a": 3, "b": 1})

    def test_summary(self):
        orders = [
            {"id": "o1", "category": "retail", "amount": "12.50"},
            {"id": "o2", "category": "retail", "amount": "3.25"},
        ]
        original = copy.deepcopy(orders)
        self.assertEqual(
            summarize_orders(orders),
            {
                "count": 2,
                "total_cents": 1575,
                "by_category_cents": {"retail": 1575},
            },
        )
        self.assertEqual(orders, original)


if __name__ == "__main__":
    unittest.main()
