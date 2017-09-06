# Introduction:

This package provides a general loggable superclass that provides Python users a simple way to persist load files with attached parameters.


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
## Basic persistance without parameters:

```
from persistable import Persistable

class SomeObject(Persistable):
	def __init__(self, workingdatadir, *args, **kwargs):
		super().__init__(workingdatadir)

	def calculating_result(self):

		self.logger.info("calculating result and persisting")

		a = 1
		b = 1
		self.payload = a + b
		self.persistload.persist(self.payload, 'absum')

	def load_result(self):
		self.payload = self.persistload.persist('absum')
```

## Persistance with file params:
```
from persistable import Persistable

class SomeObject(Persistable):
	def __init__(self, workingdatadir, *args, **kwargs):
		super().__init__(workingdatadir)

	def calculating_result(self, **params):

		self.logger.info("calculating result and persisting")

    	# Generate persistable objects:
		self.params = params
		self.payload = some_function(**params)

		# Persist with params:
		self.persistload.persist(self.payload, 'some_function', self.params)

	def load_result(self, **params):

		# Consolidate params:
    	self.params = params
    	
    	# Attempts to load exact or similar payload 
    	# (similar payload loaded if params underspecified compared to a unique model previously persisted):
    	self.payload = self.persistload.load('some_function', self.params)
```

## Persistance with dependencies:
```
from persistable import Persistable
from persistable.util import merge_dicts

class SomeObject(Persistable):
	def __init__(self, dependent_persistable_object, *args, **kwargs):
		super().__init__(from_persistable_object=dependent_persistable_object)
		self.dependent_persistable_object = dependent_persistable_object

	def calculating_result(self, **params):

		self.logger.info("calculating result and persisting")

    	# Generate persistable objects:
    	self.params = merge_dicts(params, dict(dependent_persistable_object=self.dependent_persistable_object.params))
		self.payload = some_function(self.dependent_persistable_object, **params)

		# Persist with Params:
		self.persistload.persist(self.payload, 'some_function', self.params)

	def load_result(self, **params):

		# Consolidate params:
    	self.params = merge_dicts(params, dict(dependent_persistable_object=self.dependent_persistable_object.params))

    	# Attempts to load exact or similar payload 
    	# (similar payload loaded if params underspecified compared to a unique model previously persisted):
		self.payload = self.persistload.persist('some_function', self.params)
```

# Credits:
Alex Loosely (a.loosley@reply.de)
<br>Stephan Sahm (s.sahm@reply.de)
<br>Alex Salles (a.salles@reply.de)
