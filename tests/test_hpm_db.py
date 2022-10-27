import unittest

import hpman
from hpman.hpm_db import HyperParameterOccurrence, HyperParamNode, HyperParamTree, P
from hpman.primitives import DoubleAssignmentException, EmptyValue
from hpman.source_helper import SourceHelper


class TestHyperParamNode(unittest.TestCase):
    def test_empty(self):
        node = HyperParamNode(name="test")
        self.assertEqual(node.name, "test")
        self.assertIsInstance(node.value, EmptyValue)
        self.assertEqual(len(node.db), 0)
        self.assertIs(node.get(), None)

    def test_simple(self):
        node = HyperParamNode(name="test")
        occs = [
            HyperParameterOccurrence(
                name="hp", value="value0", priority=P.PRIORITY_SET_FROM_SETTER
            ),
            HyperParameterOccurrence(
                name="hp", value="value", priority=P.PRIORITY_SET_FROM_SETTER
            ),
            HyperParameterOccurrence(
                name="hp", value=EmptyValue(), priority=P.PRIORITY_SET_FROM_SETTER
            ),
            HyperParameterOccurrence(
                name="hp", value="result", priority=P.PRIORITY_SET_FROM_CALLABLE
            ),
            HyperParameterOccurrence(
                name="hp",
                value=EmptyValue(),
                priority=P.PRIORITY_PARSED_FROM_SOURCE_CODE,
            ),
            HyperParameterOccurrence(
                name="hp", value="default", priority=P.PRIORITY_PARSED_FROM_SOURCE_CODE
            ),
        ]
        node.push(occs[-1])
        self.assertEqual(len(node.db), 1)
        self.assertEqual(node.value, "default")
        node.push(occs[-2])
        self.assertEqual(len(node.db), 2)
        self.assertEqual(node.value, "default")
        node.push(occs[-3])
        self.assertEqual(len(node.db), 3)
        self.assertEqual(node.value, "result")
        for occ in occs[:3]:
            node.push(occ)
        self.assertEqual(len(node.db), 5)
        self.assertEqual(node.value, "value")

    def test_double_assignment(self):
        node = HyperParamNode(name="test")

        occs = [
            HyperParameterOccurrence(
                name="hp",
                value="conflict",
                priority=P.PRIORITY_PARSED_FROM_SOURCE_CODE,
                lineno=1,
                filename="none",
                source_helper=SourceHelper(""),
            ),
            HyperParameterOccurrence(
                name="hp",
                value="default",
                priority=P.PRIORITY_PARSED_FROM_SOURCE_CODE,
                lineno=1,
                filename="none",
                source_helper=SourceHelper(""),
            ),
        ]

        node._check_source_code_double_assigment(occs[0])
        node.push(occs[0])
        with self.assertRaises(DoubleAssignmentException):
            node._check_source_code_double_assigment(occs[1])
