# Introduction:

This package provides a general loggable superclass that provides Python users a simple way to persist load files with attached parameters. 


# Installation:

```
git clone https://github.com/DataReply/persistable.git
cd persistable
pip install -e .
```

# Quickstart
## Basic persistance:

```
from persistable import Persistable

class SomeObject(Persistable):
	def __init__(self, workingdatadir, *args, **kwargs):
		super().__init__(workingdatadir, persistloadtype="Basic")

	def calculating_result(self):

		self.logger.info("calculating result and persisting")

		a = 1
		b = 1
		self.result = a + b
		self.persistload.persist(self.result, 'results')

	def load_result(self):
		self.result = self.persistload.persist('result')
```

## Add file params:
```
from persistable import Persistable

class SomeObject(Persistable):
	def __init__(self, workingdatadir, *args, **kwargs):
		super().__init__(workingdatadir, persistloadtype="WithParameters")

	def calculating_result(self, **params):

		self.logger.info("calculating result and persisting")

		a = 1
		b = 1
		self.result = some_function(a,b, **params)
		self.persistload.persist(self.result, 'results', params)

	def load_result(self, params):
		self.result = self.persistload.persist('result', params)
```

# Credits:
Alex Loosely (a.loosley@reply.de)
Stephan Sahm (s.sahm@reply.de)
Alex Salles (a.salles@reply.de)
