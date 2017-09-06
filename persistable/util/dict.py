from cytoolz import curry
from collections import Mapping, defaultdict

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


def recdefaultdict(*args, **kwargs):
    """ this is an awesome little trick to have a dictionary with infinitely nested default dictionaries """
    d = _cast_to_recdefaultdict(args, kwargs)
    return defaultdict(recdefaultdict, d)


def _cast_to_recdefaultdict(args, kwargs):
    """ returns casted dict in tuple wrapper or empty tuple """
    d = kwargs
    if args:
        update(d, args[0], overwrite=False)  # keep kwargs as defaults, as they follow after the args syntactically

    # change all inner dictionaries to recdefaultdict2 by recursion
    for k, v in d.items():
        if isinstance(v, Mapping):
            d[k] = recdefaultdict(v)
    return d


def update(dict1, dict2, overwrite=True, append=True):
    """ overwrites dict1 with dict2 """
    if overwrite and append:
        dict1.update(dict2)
    if overwrite and not append:
        for k in dict1:
            if k in dict2:
                dict1[k] = dict2[k]
    if not overwrite and append:
        for k in dict2:
            if k not in dict1:
                dict1[k] = dict2[k]
    return dict1


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result
