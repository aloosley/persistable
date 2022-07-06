[![Build Status](https://travis-ci.org/aloosley/persistable.svg?branch=master)](https://travis-ci.org/aloosley/persistable)
![](https://img.shields.io/badge/version-0.6.5-green.svg)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/dwyl/esta/issues)

<img src="logo.png" alt="Persistable - Programmatic Data Pipelines">

# Introduction:

This package provides users a simple framework for persisting and loading a lineage of payloads while tracking the corresponding lineage of parameters.  Payloads can be easily chained together and come with loggers by default.  Objects are uniquely and transparently identified by their parameter lineage and version.  

Hence, persistable is a capable data pipeline and model management framework.

# Installation:

```
pip install persistable
```

Note, this package requires Python 3.6+.

# How It Works:
Each Persistable object has the following features:

feature | variable | type | short note
--|--|--|--
PAYLOAD NAME | `self.payload_name` | str | Name of the payload
PAYLOAD | `self.payload` | object, recdefaultdict by default | This is what gets persisted and/or loaded
PAYLOAD PARAMETERS | `self.params` | dict | Payload parameters, including those from dependent payloads.
LOGGER | `self.logger` | Logging | A logger

The best way to understand persistable is to see some examples (or skip to the method descriptions below):

## Examples:
### 1) Basic Persistable object without parameters:

```
from persistable import Persistable
from pathlib import Path
PERSISTABLE_DATAPATH = Path('./persistable_data')


class Addition(Persistable):

	def __init__(self, workingdirname):
		super().__init__(
		    payload_name="addition",
		    workingdatapath=PERSISTABLE_DATAPATH / workingdirname
		)

	def _generate_payload(self):
		# Any self.payload defined here will automatically be persisted

		self.logger.info("calculating a persistable payload")

		# Payload Calculation:
		a = 1
		b = 1
		self.payload = a + b

		# This payload is automatically persisted

addition = Addition("test-working-dir")
addition.generate() # Persist calculate and persist the payload to storage
```

`>>> addition.payload` gives `2`

In the future, this persisted payload (albeit simple) does not have to be recalculated, and can be loaded from disk:
```
addition = Addition("test-working-dir")
addition.load()
```

`>>> addition.payload` gives `2`

---
In this example, the user created a very simple persistable object for adding two variables:
1. Inherited features from Persistable:
	```
	class Addition(Persistable)
	```
1. Constructed persistable instructing it to persist/load all payloads to path called `PERSISTABLE_DATAPATH / workingdirname`:
	```		
	super().__init__(
			payload_name="addition",
			workingdatapath=PERSISTABLE_DATAPATH / workingdirname
	)
	```
1. Define the payload by overriding `_generate_payload(self, **untracked_payload_params)`.  When `addition.generate()` is called later, the payload is calculated from `_generate_payload(self, **untracked_payload_params)` and automatically persisted.


### 2) Persistable object with params:
Usually you'll want to pass parameters to your persistable object:

```
from persistable import Persistable
from pathlib import Path
PERSISTABLE_DATAPATH = Path('./persistable_data')

class Addition(Persistable):

	def __init__(self, workingdirname, params, verbose=True):
		"""
		This class adds two params together.

		Parameters
		----------
		workingdirname : str
				Directory name where persisted payloads and logs are stored.

		params         : dict
				Required Keys
				-------------
				a   : int or float
				b   : int or float
		verbose         : bool
				Verbosity flag
		"""

	  # Construct persistable:
		super().__init__(
			payload_name="addition", params=params
			workingdatapath=PERSISTABLE_DATAPATH / workingdirname,
			verbose=verbose
		)

		# Check required params provided:
		self._check_required_params(['a', 'b'])

	def _generate_payload(self):

		self.logger.info("calculating a persistable payload")

		a = self.params['a']
		b = self.params['b']
		self.payload = a + b

addition = Addition("test-working-dir", {"a": 1, "b": 2})
addition.generate() # Persist calculate and persist the payload to storage
```

`>>> addition.payload` gives `3`

The only difference between this example and example 1) is that now there are user defined parameters.  The required params, `a` and `b`, are passed through the params dict.  Once the result has been generated (and therefore persisted), it can be immediately loaded without recalculation.

```
addition = Addition("test-working-dir", {"a": 1, "b": 2})
addition.load()
```

`>>> addition.payload` gives `3`

For convenience, there is also a generate_load() method which first tries to load the payload, and then generates if the payload has not yet been persisted.  Keep in mind, the payload is uniquely identified by `payload_name` and it's params.

```
addition = Addition("test-working-dir", {"a": 1, "b": 5})
addition.generate_load()
```

`>>> addition.payload` gives `6`

### 3) Persistable object with dependencies:
Users can build Persistable Object that depend on other persistables and the params lineage will be automatically maintained:

```
from persistable import Persistable


class IsPrimeNumber(Persistable):

	def __init__(self, persistable_object_containing_int_for_payload, params):
        super().__init__(
            payload_name="isprime",
            params=params,
            from_persistable_object=persistable_object_containing_int_for_payload
        )

        self.dependency = persistable_object_containing_int_for_payload

	def _generate_payload(self):

		self.logger.info("calculating a persistable payload")
		self.payload = is_prime(self.dependency.payload)

def is_prime(num: int)
	if num > 1:
	   for i in range(2,num):
	       if (num % i) == 0:
	           return False
	   else:
	       return True
	else:
	   return False


addition = Addition("test-working-dir", {"a": 1, "b": 2})
addition.load_generate() # Persist calculate and persist the payload to storage

is_prime_number = IsPrimeNumber(addition, {})
is_prime_number.generate() # Persist calculate and persist the payload to storage
```

Now, the payload can be loaded again without calculation by chaining:
```
addition = Addition("test-working-dir", {"a": 1, "b": 2})
is_prime_number = IsPrimeNumber(addition, {})
is_prime_number.load() # Load the payload from storage later
```

## Persistable Methods:
#### self.persist()
```
Persists the payload in it's current state.
```

#### self.generate(persist: bool=True, **untracked_payload_params):
```
Generates payload and (by default) persists it.

Parameters
----------
persist                     : bool
		Default True, the payload is persisted
untracked_payload_params    : dict
		These are helper parameters for generating an object that are not tracked.  
		Generally these are not used.
```

#### self.load(**untracked_payload_params)
```
Loads persisted payload

Parameters
----------
untracked_payload_params    : dict
		Parameters not tracked by persistable that are only used to run the _postload_script.
		Such scripts are useful if part of the payload cannot be persisted and needs to be recalculated
		at load time.
```

#### self.load_generate(**untracked_payload_params)
```
Like load() but executes the generate() method if load() fails due to a FileNotFoundError.
```

#### self.update_fn_params(new_fn_params: dict, delete_old: bool=True)
```
Updates fn_params (that uniquely define the payload along with the payload_name) and renames the persisted
payload file accordingly.

Convenience method when, during development, parameter names or values are refactored but the developer
does not wishs to regenerate all her persistable payloads.

Parameters
----------
new_fn_params   : dict
    New fn_params to pin to the Persistable object.
delete_old      : bool
    Use False to keep old parameterized payload file (sometimes useful for backwards compatibility).
    Use True to remove the old parameterized payload file (garbage collecting and storage friendly default).
```

#### self.update_payload_name(new_payload_name: str, delete_old: bool=True)
```
Updates payload_name (that uniquely define the payload along with the fn_params) and renames the persisted
payload file accordingly.

Convenience method when, during development, parameter names or values are refactored but the developer
does not wishs to regenerate all her persistable payloads.

Parameters
----------
new_payload_name    : str
    New payload_name to pin to the Persistable object
delete_old          : bool
    Use False to keep old parameterized payload file (sometimes useful for backwards compatibility).
    Use True to remove the old parameterized payload file (garbage collecting and storage friendly default).
```

#### self.reset_payload()
```
Removes payload from memory.

Useful, for example, if the user wants to keep a Persistable instance without the payload state (and its 
corresponding memory overhead).

This can be useful for create an out-of-core calculation.
```

## Other persistable methods and properties:
* `self.fn_params` (dict) - This uniquely defines the persistable filename hash for the persisted payload.  It is typically identical to `self.params` unless modified with the `excluded_fn_params` kwarg in the Persistable constructor.
* `self.__getitem__(item)` - returns item from `self.payload`
* `self.payload_keys` (dict_keys or None) - Convenience property that returns `self.payload.keys()` if the payload is a dictionary.
* `self._generate_payload(**untracked_payload_params)` - This method defines the payload generated (and persisted) when `self.generate(**untracked_payload_params)` is called.`
* `self._postload_script(**untracked_payload_params)` - Define here any extra algorithmic steps to run after loading the payload

# Conclusion:
In general, the benefit to using `Persistable` is maximal when:
* payload generation is computationally expensive payload and would benefit by doing so only once
* it's important to keep track of pipeline parameters and versions and have results accessible later (i.e. persisted)

# Credits:
Alex Loosely (a.loosley@reply.de)
<br>Stephan Sahm (s.sahm@reply.de)
<br>Alex Salles (a.salles@reply.de)
