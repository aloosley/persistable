from cytoolz import curry
from collections import Mapping

@curry
def recvalmap(func, d, factory=dict):
    """ Apply function to values of dictionary

    >>> bills = {"Alice": {"Schmidt": [20, 15], "Smith": [30]}, "Bob": [10, 35]}
    >>> recvalmap(sum, bills)  # doctest: +SKIP
    {'Alice': {"Schmidt": 35, "Smith": 30}, 'Bob': 45}

    See Also:
        reckeymap
    """
    rv = factory()
    for k, v in d.items():
        if isinstance(v, Mapping):
            rv[k] = recvalmap(func, v, factory=factory)
        else:
            rv[k] = func(v)
    return rv

@curry
def reckeymap(func, d, factory=dict):
    """ Apply function to keys of dictionary

    >>> bills = {"Alice": {"Schmidt": [20, 15], "Smith": [30]}, "Bob": [10, 35]}
    >>> reckeymap(str.lower, bills)  # doctest: +SKIP
    {'alice': {"schmidt": [20, 15], "smith": [30]}, 'bob': [10, 35]}

    See Also:
        recvalmap
    """
    rv = factory()
    for k, v in d.items():
        newk = func(k)
        if isinstance(v, Mapping):
            rv[newk] = reckeymap(func, v, factory=factory)
        else:
            rv[newk] = v
    return rv