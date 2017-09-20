# Introduction:

This package provides a general loggable superclass that provides Python users a simple way to persist load calculations and track corresponding calculation parameters.


# Installation:

```
pip install persistable
```

Note, this package has only been tested with Python 3.6+.

# Benefits:
Inheriting from Persistable automatically spools a logger and appends the PersistLoad object for easy and reproducible data persistance with loading, with parameter tracking.  The PersistLoad object is based on setting a `workingdatadir` within which all persisted data is saved and logs are stored.  Such a directory acts as a home for a specific set of experiments.

Each Persistable object has the following features:

feature | variable | type
--|--|--
LOGGER | self.logger | Logging
PERSISTABLE PAYLOAD | self.payload | recdefaultdict by default
PAYLOAD NAME | self.payload_name | str
FILENAME TAGS | self.params | dict
PERSISTLOAD OBJECT | self.persistload | PersistLoad
PERSIST TOOL | self.persistload.persist(payload, name, params) | . 
LOAD TOOL | self.persistload.load(name, params)	| object

# Examples:
## Basic Persistable object without parameters:

```
from persistable import Persistable
from pathlib import Path


class Addition(Persistable):
	LOCALWORKINGDIR = Path('.')

	def __init__(self, workingdirname):
		super().__init__(payload_name="addition", workingdatapath=self.LOCALWORKINGDIR / workingdirname)

	def _generate_payload(self):

		self.logger.info("calculating a persistable payload")

		a = 1
		b = 1
		self.payload = a + b

addition = Addition("test-working-dir")
addition.generate() # Persist calculate and persist the payload to storage
# addition.load() # Load the payload from storage
```

`>>> addition.payload` gives `2`

## Persistable object with params:
Usually you'll want to pass parameters to your persistable object:

```
from persistable import Persistable
from pathlib import Path


class Addition(Persistable):
	LOCALWORKINGDIR = Path('.')

	def __init__(self, workingdirname, params):
		super().__init__(
			payload_name="addition", params=params
			workingdatapath=self.LOCALWORKINGDIR / workingdirname
		)

	def _generate_payload(self):

		self.logger.info("calculating a persistable payload")

		a = self.params['a']
		b = self.params['b']
		self.payload = a + b

addition = Addition("test-working-dir", {"a": 1, "b": 2})
addition.generate() # Persist calculate and persist the payload to storage
# addition.load() # Load the payload from storage
```

`>>> addition.payload` gives `3`


## Persistable object with dependencies:
Users can build Persistable Object that depend on other objects:

```
from persistable import Persistable
from pathlib import Path

class IsPrimeNumber(Persistable):
	LOCALWORKINGDIR = Path('.')

	def __init__(self, params, persistable_object_containing_int_for_payload):
        super().__init__(
            payload_name="isprime",
            params=params,
            from_persistable_object=persistable_object_containing_int_for_payload
        )

        self.dependency = persistable_object_containing_int_for_payload

	def _generate_payload(self):

		self.logger.info("calculating a persistable payload")
		self.payload = is_prime(self.dependency.payload)

def is_prime(num)
	if num > 1:
	   for i in range(2,num):
	       if (num % i) == 0:
	           return False
	   else:
	       return True
	else:
	   return False


is_prime_number = IsPrimeNumber("test-working-dir", {"a": 1, "b": 2})
is_prime_number.generate() # Persist calculate and persist the payload to storage
# is_prime_number.load() # Load the payload from storage
```

## Conclusions:
In general, the benefit to using `Persistable` comes when the user defines an expensive `_generate_payload()` and the user will want to query the payload later. 

# Credits:
Alex Loosely (a.loosley@reply.de)
<br>Stephan Sahm (s.sahm@reply.de)
<br>Alex Salles (a.salles@reply.de)
