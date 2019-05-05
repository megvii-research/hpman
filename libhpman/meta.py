import functools


class dict_attr_binding_class(type):
    """Metaclass to provide bi-directional binding between property-annotated
    class attributes and dict items. A concrete example is as follows (and will
    be doctest-ed):

        .. code::
            >>> class MyDictBindingClass(metaclass=dict_attr_binding_class):
            ...    # bi-directionally binds `obj['name']` and obj.name
            ...    name: property = 1
            ...
            ...    # bi-directionally binds `obj['hello']` and obj.hello
            ...    hello: property = 'world'
            ...
            ...    # `value` is a normal attribute
            ...    value = 3
            ...
            ...    # some normal property
            ...    @property
            ...    def func(self):
            ...        return "Hello World!"
            ...
            >>> x = MyDictBindingClass()
            >>> x
            {'name': 1, 'hello': 'world'}
            >>>
            >>> # Test attribute `name`
            >>> x['name'] = 'apricots'
            >>> x
            {'name': 'apricots', 'hello': 'world'}
            >>> x.name
            'apricots'
            >>> x['name']
            'apricots'
            >>>
            >>> # Test attribute `hello`
            >>> x.hello = "What's up?"
            >>> x.hello
            "What's up?"
            >>> x
            {'name': 'apricots', 'hello': "What's up?"}
            >>>
            >>> # Test normal attribute `value`
            >>> x.value
            3
            >>> x.value = 2
            >>> x.value
            2
            >>> x
            {'name': 'apricots', 'hello': "What's up?"}
            >>> x['value'] = 42
            >>> x
            {'name': 'apricots', 'hello': "What's up?", 'value': 42}
            >>> x.value
            2
    """

    def __new__(cls, name, bases, dct):
        if dict not in bases:
            bases = bases + (dict,)

        binded = {}
        # make bindings
        if "__annotations__" in dct:
            for k, v in dct["__annotations__"].items():
                if v == property:
                    binded[k] = dct[k]
                    dct[k] = cls._make_binding(cls, k, dct[k])
        if len(binded) == 0:
            return super().__new__(cls, name, bases, dct)

        # find old init function to be injected
        if "__init__" in dct:
            old_init = dct["__init__"]
        else:

            def old_init(self, *args, **kwargs):
                super(type(self), self).__init__(*args, **kwargs)

            old_init.__doc__ = "Generated init function for `{}`".format(name)

        # hook init function to inject default values
        @functools.wraps(old_init)
        def new_init(self, *args, **kwargs):
            old_init(self, *args, **kwargs)
            for k, v in binded.items():
                if k not in self:
                    self.__setitem__(k, v)

        dct["__init__"] = new_init

        return super().__new__(cls, name, bases, dct)

    def _make_binding(cls, name, default_value):
        """Create bi-directional binding in using property"""

        def getter(self):
            return self.__getitem__(name)

        def setter(self, v):
            return self.__setitem__(name, v)

        # TODO: deleter

        doc = "Binded property to `{}` in dict".format(name)
        return property(getter, setter, doc=doc)
