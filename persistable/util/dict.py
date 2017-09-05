from cytoolz import curry
from collections import Mapping

@curry
def recursive_value_map(func, d, factory=dict):
    """ Apply function to values of dictionary

    >>> bills = {"Alice": {"Schmidt": [20, 15], "Smith": [30]}, "Bob": [10, 35]}
    >>> recursive_value_map(sum, bills)  # doctest: +SKIP
    {'Alice': {"Schmidt": 35, "Smith": 30}, 'Bob': 45}

    See Also:
        recursive_key_map
    """
    rv = factory()
    for k, v in d.items():
        if isinstance(v, Mapping):
            rv[k] = recursive_value_map(func, v, factory=factory)
        else:
            rv[k] = func(v)
    return rv

@curry
def recursive_key_map(func, d, factory=dict):
    """ Apply function to keys of dictionary

    >>> bills = {"Alice": {"Schmidt": [20, 15], "Smith": [30]}, "Bob": [10, 35]}
    >>> recursive_key_map(str.lower, bills)  # doctest: +SKIP
    {'alice': {"schmidt": [20, 15], "smith": [30]}, 'bob': [10, 35]}

    See Also:
        recursive_value_map
    """
    rv = factory()
    for k, v in d.items():
        newk = func(k)
        if isinstance(v, Mapping):
            rv[newk] = recursive_key_map(func, v, factory=factory)
        else:
            rv[newk] = v
    return rv