import random
import unittest

import hpman
from hpman.hpm_db import HyperParameterDB, HyperParameterOccurrence, L, P


class TestHPMDB(unittest.TestCase):
    def _make_db(self, data):
        db = HyperParameterDB()
        for d in data:
            db.push_occurrence(HyperParameterOccurrence(**d))
        return db

    def _make_random_db(self, seed):
        s = random.getstate()

        random.seed(seed)
        n = random.randint(10, 20)
        random.setstate(s)

    def setUp(self):
        self.db = self._make_db(
            [
                dict(name="v10", value=0, priority=P.PRIORITY_PARSED_FROM_SOURCE_CODE),
                dict(name="v11", value=1, priority=P.PRIORITY_PARSED_FROM_SOURCE_CODE),
                dict(name="v11", priority=P.PRIORITY_PARSED_FROM_SOURCE_CODE),
                dict(name="v12", value=2, priority=P.PRIORITY_PARSED_FROM_SOURCE_CODE),
                dict(name="v13", priority=P.PRIORITY_PARSED_FROM_SOURCE_CODE),
                dict(name="v20", value=0, priority=P.PRIORITY_SET_FROM_CALLABLE),
                dict(name="v21", value=1, priority=P.PRIORITY_SET_FROM_CALLABLE),
                dict(name="v21", value=2, priority=P.PRIORITY_SET_FROM_CALLABLE),
                dict(name="v22", value=3, priority=P.PRIORITY_SET_FROM_CALLABLE),
                dict(name="v30", value=0, priority=P.PRIORITY_SET_FROM_SETTER),
                dict(name="v31", value=1, priority=P.PRIORITY_SET_FROM_SETTER),
                dict(name="v31", value=2, priority=P.PRIORITY_SET_FROM_SETTER),
                dict(name="v32", value=3, priority=P.PRIORITY_SET_FROM_SETTER),
            ]
        )

    def test_construction(self):
        pass

    def test_select(self):
        db = self.db
        self.assertEqual(len(db.select(L.has_default_value)), 3 + 3 + 3)

        self.assertEqual(
            len(db.select(L.of_priority(P.PRIORITY_PARSED_FROM_SOURCE_CODE))), 5
        )

        self.assertEqual(len(db.select(L.of_priority(P.PRIORITY_SET_FROM_CALLABLE))), 3)

        self.assertEqual(len(db.select(L.of_priority(P.PRIORITY_SET_FROM_SETTER))), 3)

    def test_group_by(self):
        db = self.db

        self.assertEqual(len(db.group_by("value")), 4 + 1)  # {0,1,2,3,EmptyValue}

        self.assertEqual(len(db.group_by("priority")[P.PRIORITY_SET_FROM_SETTER]), 3)

        self.assertEqual(
            len(db.group_by("priority")[P.PRIORITY_PARSED_FROM_SOURCE_CODE]), 5
        )

    def test_indexing(self):
        db = self.db
        self.assertEqual(db.indexing(0).name, "v10")
        self.assertEqual(db.indexing(-1).name, "v32")
        self.assertEqual(len(db.indexing([1, 2, 3])), 3)
        self.assertRaises(IndexError, db.indexing, "a")

    def test_extract_column(self):
        db = self.db
        self.assertListEqual(db.indexing([0, 5, 8]).extract_column("value"), [0, 0, 0])

    def test_choose_columns(self):
        db = self.db
        self.assertListEqual(
            db.choose_columns("name", "value")
            .indexing([0, 5, 8])
            .extract_column("value"),
            [0, 0, 0],
        )

    def test_apply(self):
        db = self.db
        self.assertTrue(
            all(
                i.endswith(".modified")
                for i in db.copy()
                .apply(L.apply_column("name", lambda x: x + ".modified"))
                .extract_column("name")
            )
        )

        d = db.select(L.has_default_value)
        gt = sum(d.extract_column("value")) + len(d) * 1
        pred = sum(
            d.apply(L.apply_column("value", lambda x: x + 1)).extract_column("value")
        )
        pred2 = sum(d.extract_column("value"))
        self.assertEqual(pred, gt)
        self.assertEqual(pred2, gt)

    def test_reduce(self):
        db = self.db

        # with initial value
        d = db.select(L.has_default_value)
        self.assertEqual(
            sum(d.extract_column("value")),
            d.reduce(lambda a, b: a + b.value, initial=0),
        )

        # with intial value and no entries in db
        self.assertEqual(
            123, HyperParameterDB().reduce(lambda a, b: a + b.value, initial=123)
        )

        # without initial value and
        self.assertRaises(ValueError, HyperParameterDB().reduce, lambda a, b: a)

        self.assertEqual(db.reduce(lambda a, b: a)["name"], "v10")

    def test_misc(self):
        db = self.db

        # empty
        self.assertEqual(HyperParameterDB().empty(), True)
        self.assertEqual(db.empty(), False)

        # all
        self.assertFalse(db.all(L.has_default_value))
        self.assertTrue(db.all(lambda row: len(row.name) == 3))

        # any
        self.assertTrue(db.any(L.has_default_value))
        self.assertFalse(db.all(lambda row: len(row.name) == 2))

        # find_first
        self.assertEqual(db.find_first(L.of_value(2))["name"], "v12")
        self.assertEqual(db.find_first(L.of_value(4)), None)

        # logic operators
        self.assertEqual(
            db.find_first(L.land(L.has_default_value, L.of_name_suffix("2")))["value"],
            2,
        )

        self.assertEqual(
            db.select(L.land(L.of_value(2), L.of_name_prefix("v3")))[0]["priority"],
            P.PRIORITY_SET_FROM_SETTER,
        )

        self.assertEqual(db.count(L.lor(L.of_value(2), L.of_name_suffix("2"))), 5)

        self.assertEqual(
            db.count(L.lnot(L.lor(L.of_value(2), L.of_name_suffix("2")))), len(db) - 5
        )
