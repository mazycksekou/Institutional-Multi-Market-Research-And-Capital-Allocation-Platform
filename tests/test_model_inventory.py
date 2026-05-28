import unittest
from model_governance.model_inventory import get_model_inventory, GROUPS

class TestModelInventory(unittest.TestCase):
    def test_groups_registered(self):
        inv = get_model_inventory()
        got = {i['group'] for i in inv}
        self.assertTrue(set(GROUPS).issubset(got))
