from .dict import recursive_key_map
from .higher_level import LazyProxy
from collections import Mapping
from hashlib import md5
import pyparsing as pp

# Wrappers for PersistLoad
# ------------------------


SHORTEN_PARAM_MAP = {
    "random_state": "rndst",
    "datasource": "dsrc",
    "datafilespath": "dfpath",
    "experimentname": "exname",
    "datasetname": "dsname",
    "concat_pulses": "ccps",
    "samplesize": "ssz"
}


def default_standard_filename(fn_type, fn_ext=None, shorten_param_map=SHORTEN_PARAM_MAP, **fn_params):
    """ this follows the parameter convention setup in LocalDataSaveLoad

    not that parameter shortening is not reverted automatically due to principle loss of information """

    # Set fn_ext from defaults and add '.'
    if fn_ext is None:
        fn_ext = "pkl"
    if not fn_ext.startswith('.'):
        fn_ext = f".{fn_ext}"

    # Ensure there are no overlaps between fn_param names and the SHORTEN_PARAM_MAP
    # (This could otherwise cause naming conflicts):
    for k, shortk in shorten_param_map.items():
        if k in fn_params and shortk in fn_params:
            # we have to raise this, as otherwise parameters from fn_params are lost
            # by overwriting the same shortened key
            raise ValueError("You use both long and short version of a parameter name within ``fn_params``. "
                             "Consider changing ``util.os_util.SHORTEN_PARAM_MAP`` to get rid of this error.")

    # Create fn:
    fn_params_shortnames = _convert_listlike_fn_params(recursive_key_map(lambda k: shorten_param_map.get(k, k), fn_params))
    fn = f"{fn_type}{dict_to_fnsuffix(fn_params_shortnames)}{fn_ext}"

    # Check length to avoid windows errors:
    # (Update: length is now handled properly at the persistload level)
    # if len(fn) > 255:
    #     raise OSError(
    #         "Windows may not support longer filenames than 255.  One solution may be to shorten parameters "
    #                   "by adding to SHORTEN_PARAMETER_MAP \n FileName = {fn}".format(fn=fn)
    #     ) # See https://msdn.microsoft.com/en-us/library/windows/desktop/aa365247(v=vs.85).aspx for further information
    for windows_forbidden_char in ("<", ">"):
        if windows_forbidden_char in fn:
            raise OSError(f"Unfortunately you used char '{windows_forbidden_char}' which is forbidden for filenames on Windows Systems. Filename was '{fn}'")
    return fn

def handle_long_fn(fn, fn_type):
    """
    If the filename is long, this returns a truncated version and it's corresponding txt file for 
    storing the nontruncated parameters

    :param fn: 
    :return: (bool, str, str or None)
        is_longfilename, filename_to_save, filename_for_params
    """

    # Check length to avoid errors with older versions of Windows:
    # (See https://msdn.microsoft.com/en-us/library/windows/desktop/aa365247(v=vs.85).aspx for further information)
    if len(fn) > 255:
        fn_ext = fn.split('.')[-1]
        fn_hashed_name = f"{fn_type}_truncatedHash({md5(fn.encode()).hexdigest()})"

        return True, (
            f"{fn_hashed_name}.{fn_ext}",
            f"{fn_hashed_name}.params"
        )
    else:
        return False, (fn, None)

def _convert_listlike_fn_params(fn_params):
    converted_fn_params = {}
    for key in fn_params:
        # Convert anything with a length to true:
        if isinstance(fn_params[key], dict):
            converted_fn_params[key] = _convert_listlike_fn_params(fn_params[key])
            continue

        # If parameter is list-like (and not a string), convert it to True:
        try:
            if len(fn_params[key]) > 3 and not isinstance(fn_params[key], str):
                converted_fn_params[key] = True
            else:
                converted_fn_params[key] = fn_params[key]
        except:
            converted_fn_params[key] = fn_params[key]

    return converted_fn_params



# STANDARD FILENAME CONVENTION
# ============================

# Dictionary to filename suffix:

def dict_to_fnsuffix(d):
    """ When possible, map parameter names to shortened names and return parsed filename

    works with nested dictionaries now
    CAUTION: Only Variable Names are supported as keys (also for nested dictionaries) """
    return "{%s}" % ",".join(
        "{0}={1}".format(
            k,
            dict_to_fnsuffix(d[k]) if isinstance(d[k], Mapping) else repr(d[k])
        )
        for k in sorted(d.keys())
    )


# def _deprecated_construct_fnsuffix_parser():
#     nested_dict = pp.Forward()
#     key = pp.Regex(r"\w*")
#     # value = pp.quotedString | nested_dict | pp.Regex(r"[^=,]+")
#     value = pp.quotedString | pp.Regex(r"[^=,{}]+") | nested_dict
#     # item = key("key") + pp.Suppress("=") + value("value")
#     item = pp.Dict(pp.Group(key + pp.Suppress("=") + value))
#     items = pp.delimitedList(item)
#     nested_dict << (pp.Suppress("{") + items + pp.Suppress("}"))
#     return nested_dict + pp.StringEnd()

def _construct_fnsuffix_parser():
    atom = pp.Regex(r"[^=,{}()[\]]+")
    value = pp.Forward().setName("value")  # .setDebug()

    key = pp.Regex(r"\w*").setName("key")  # .setDebug()
    item = pp.Dict(pp.Group(key + pp.Suppress("=") + value))
    items = pp.delimitedList(item)
    dict_ = pp.Suppress("{") + items + pp.Suppress("}")

    list_, tuple_, set_ = (o + pp.delimitedList(value, combine=True) + c
                           for o, c in zip(["[", "(", "{"], ["]", ")", "}"]))

    combine_values = [pp.Combine(expr) for expr in (list_, tuple_, set_, atom + value)]
    value << (pp.quotedString | dict_ | pp.Or(combine_values) | atom)  # Caution: brackets are needed because of << operator precedence!!
    return dict_ + pp.StringEnd()

_fndict_parser = LazyProxy(_construct_fnsuffix_parser)

# Filename suffix to dictionary:
def fnsuffix_to_dict(string):
    """ Note that this is leaving values unevaluated

    reasons:
    - literal_eval might break on certain values
    - eval would be crucially insecure
    - we only need rough dict parsing
    """
    if not string:
        return {}
    return _fndict_parser.parseString(string).asDict()


def parse_standard_filename(fn):
    """
    This is the inverse of default_standard_filename
    
    Parses a standard file with sorted dictionary-like parameter specification.
    Dictionary sorting ensures unique filenames for equivalent parameter-value sets.

    Parameters
    ----------
    fn : str
        complete filename

    Returns
    -------
    tuple (str, str, dict)
        (name, extension, kwargs)
        note that extension contains leading dot, following python's default behaviour
        note that kwargs values are unevaluated strings
    """
    a = fn.find("{")
    b = fn.rfind("}") + 1
    if a == -1 or b == 0:  # no curly brackets found
        c = fn.rfind(".")
        return fn[:c], fn[c:], {}
    fn_params = fnsuffix_to_dict(fn[a:b])
    # return fn[:a], fn[:b], fn_params
    return fn[:a], fn[b:], recursive_key_map(lambda k: SHORTEN_PARAM_MAP.get(k, k), fn_params, factory=dict)

