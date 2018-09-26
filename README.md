# Introduction:

This package provides users a simple framework for persisting and loading a lineage of payloads while tracking the corresponding lineage of parameters.  Payloads can be easily chained together and come with loggers by default.  Objects are uniquely and transparently identified by their parameter lineage and version making persistable also a capable model, transformer, or data-view management framework.

# Installation:

```
pip install persistable
```

Note, this package requires Python 3.6+.

# How It Works:
Each Persistable object has the following important features:

feature | variable | type | short note
--|--|--
LOGGER | self.logger | Logging | A logger
PERSISTABLE PAYLOAD | self.payload | object, recdefaultdict by default | This is the **payload** that gets persisted and/or loaded
PAYLOAD NAME | self.payload_name | str | Name of the payload
FILENAME TAGS | self.params | dict | Payload parameters, these along with the payload name uniquely identify the payload

The best way to understand persistable is to see some examples:

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

## Conclusion:
In general, the benefit to using `Persistable` is maximal when:
* payload generation is computationally expensive payload and would benefit by doing so only once
* it's important to keep track of pipeline parameters and versions and have results accessible later (i.e. persisted)


# Credits:
Alex Loosely (a.loosley@reply.de)
<br>Stephan Sahm (s.sahm@reply.de)
<br>Alex Salles (a.salles@reply.de)
