#!/usr/bin/env python
# -*- coding: utf-8 -*-
from cytoolz import curry
from wrapt import ObjectProxy
from functools import wraps


def call(func, *args, **kwargs):
    return func(*args, **kwargs)

@curry
def funcmap(func, func1, *other_funcs):
    """ map implementation to work with functions as contexts """
    contexts = (func1,) + other_funcs

    @wraps(func1)
    def generic_func(*args, **kwargs):
        return func(*(con(*args, **kwargs) for con in contexts))

    generic_func.contexts = contexts
    return generic_func


# Predicates
# ==========

def attribute_checker(**attr_in):
    """
    With this helper you can easily build predicates according to attributes.

    Examples
    --------
    use it to generate predicate functions
    >>> pred = attribute_checker(isin={1, "zwei"}, name="myname")
    say you have an arbitrary instance
    >>> class Empty:
    >>>     pass
    >>> e = Empty()
    >>> e.isin = 1
    then all given ``attr_in`` must be true
    >>> pred(e)
    ... False
    >>> e.name="myname"
    >>> pred(e)
    ... True

    Parameters
    ----------
    attr_in : kwargs
        lists and sets are checked with ANY/OR, everything else is checked directly
        single kwargs are combined by ALL/AND

        use name=value for checking a specific value
        use name=[eitherthis, orthis, orthis, ...] for attr ``name`` being one of the values
        same for name={this, orthat, ...\

    Returns
    -------
    predicate function
    """
    def comp(v, l):
        if isinstance(l, (list, set)):
            return v in l
        return v == l

    def check(o):
        return any(comp(getattr(o, attr), l) for attr, l in attr_in.items())

    return check


class LazyProxy(ObjectProxy):
    """ this is an amazing class which allows you to postpone the initalization of an object
    until an attribute of it is asked for or it is called like a function """

    def __init__(self, initializer, *args, **kwargs):
        self._self_initializer = initializer
        self._self_init_args = args
        self._self_init_kwargs = kwargs

    @property
    def is_initialized(self):
        try:
            # the super is necessary here, otherwise we get an infinite loop
            super(LazyProxy, self).__wrapped__
            return True
        except ValueError:
            return False

    def initialize(self):
        super(LazyProxy, self).__init__(self._self_initializer(*self._self_init_args, **self._self_init_kwargs))

    # overwrite all entry points into an object
    # -----------------------------------------
    # TODO add more as you find them

    for name in ("__getitem__", "__setitem__", "__delitem__", "__len__", "__contains__", "__str__"):
        code = """
def {name}(self, *args):
    if not self.is_initialized:
        self.initialize()
    return self.__wrapped__.{name}(*args)
""".format(name=name)
        exec(code)

    def __call__(self, *args, **kwargs):
        if not self.is_initialized:
            self.initialize()
        return self.__wrapped__(*args, **kwargs)

    def __getattr__(self, item):
        if not self.is_initialized:
            self.initialize()
        return getattr(self.__wrapped__, item)

    __repr__ = __str__

LazyCaller = LazyProxy


@curry
def convert(elm, type):  # syntax should mimick isinstance
    if isinstance(elm, type):
        return elm
    return type(elm)



from contextlib import contextmanager
import inspect


@contextmanager
def change_locals(**temp_locals):
    """ Binds the variable within the context-manager only and returns to default locals on exit

    can be nested

    Parameters
    ----------
    temp_locals : arbitrary keyword arguments
        are interpreted as variable assignments

    Returns
    -------
    contextmanager
    """
    frame = inspect.currentframe()
    try:
        nonlocals = frame.f_back.f_back.f_locals  # 2x .f_back because of context_manager
        restore = {}
        delete = []
        for k, v in temp_locals.items():
            if k in nonlocals:
                restore[k] = nonlocals[k]
            else:
                delete.append(k)
            nonlocals[k] = v

        yield

        for k, v in restore.items():
            nonlocals[k] = v
        for k in delete:
            del nonlocals[k]
    finally:
        # adapted from http://stackoverflow.com/questions/6618795/get-locals-from-calling-namespace-in-python
        del frame


def instance_context(instance):
    """ given an instance it populates all instance methods directly within the with-scope
    i.e. instead of instance.function() you can just directly call function()

    Parameters
    ----------
    instance : arbitrary
        to be populated

    Returns
    -------
    contextmanager
    """
    return change_locals(**{attr: getattr(instance, attr) for attr in dir(instance) if not attr.startswith("_")})



class classproperty(ObjectProxy):
    """ decorator which turns given function into a class property

    does work with abc.abstractmethod
    however does not support setter (in fact this is in general not possible without MetaClasses in current python version)

    >>> class A:
    >>>     @classproperty
    >>>     def myattr(cls):
    >>>         return cls.__name__
    >>>
    >>> print(A.myattr)
    A
    """
    def __get__(self, instance, cls):
        return self.__wrapped__(cls)