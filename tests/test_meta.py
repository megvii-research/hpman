import unittest
import libhpman
from libhpman import meta


class TestMeta(unittest.TestCase):
    def test_dict_attr_binding_class(self):
        # Tests here are complementary to the doctests in
        # `libhpman.meta.dict_attr_binding_class`
        class Dict(metaclass=meta.dict_attr_binding_class):
            name: property = 1
            value: str = 2  # should of no use

            def __init__(self, what):
                self.what = what

        obj = Dict("hello")
        self.assertEqual(obj.what, "hello")

        self.assertNotIn("value", obj)
        self.assertNotIn("what", obj)

        obj.what = 1
        self.assertNotIn("what", obj)
        obj["what"] = 3
        self.assertEqual(obj.what, 1)
        self.assertEqual(obj["what"], 3)

    def test_dict_attr_binding_class_no_annotation(self):
        class Dict(metaclass=meta.dict_attr_binding_class):
            name = 2

        obj = Dict()
        self.assertNotIn("name", obj)

    def test_dict_attr_binding_class_with_init(self):
        class Dict(metaclass=meta.dict_attr_binding_class):
            name: property = 2

        obj = Dict({"name": 1})
        self.assertEqual(obj["name"], 1)
