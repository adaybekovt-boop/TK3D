from __future__ import annotations

import unittest

from geoforge.spec import derive_entity_seed


class SeedTests(unittest.TestCase):
    def test_seed_is_stable(self) -> None:
        first = derive_entity_seed(42, "room.main", "room", "1.0.0")
        second = derive_entity_seed(42, "room.main", "room", "1.0.0")
        self.assertEqual(first, second)

    def test_seed_is_entity_local(self) -> None:
        room = derive_entity_seed(42, "room.main", "room", "1.0.0")
        other = derive_entity_seed(42, "room.other", "room", "1.0.0")
        changed_builder = derive_entity_seed(42, "room.main", "room", "1.0.1")
        self.assertNotEqual(room, other)
        self.assertNotEqual(room, changed_builder)


if __name__ == "__main__":
    unittest.main()

