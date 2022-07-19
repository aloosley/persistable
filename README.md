[![Build Status](https://travis-ci.org/aloosley/persistable.svg?branch=master)](https://travis-ci.org/aloosley/persistable)
![](https://img.shields.io/badge/version-0.6.5-green.svg)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/dwyl/esta/issues)

<img src="logo.png" alt="Persistable - Programmatic Data Pipelines">

# Introduction

This package provides users a simple framework for persisting and loading a
payloads that come from a lineage of generation pipelines, each with there own
set of parameters.  Persistable helps developers define those pipelines,
track those parameters, and reproducibly generate, persist, and load their
payloads.

Hence, persistable is a lightweight data pipeline and payload
(i.e. dataset or model) management framework.

# Installation

```
pip install persistable
```

Note, this package requires Python 3.9+.

# How It Works
Each Persistable object has the following feature:

feature | attribute | type | short note
--|--|--|--
PAYLOAD | `self.payload` | `Generic` | This is what gets generated, persisted and/or loaded.
PARAMETERS | `self.params` | `PersistableParams` | Parameters that define payload generation (not including parameters from upstream payloads)
PARAMETERS TREE | `self.params_tree` | `dict` | Parameters that define payload generation (including parameters from tracked persistable dependencies)
PAYLOAD NAME | `self.payload_name` | `str` | Name of the payload (defaults to class name).
PAYLOAD IO | `self.payload_io` | `FileIO` | FileIO used to persist and load payload (defaults to a robust PickleFileIO so the user does not have to manage IO unless she chooses to). Cloud FileIOs can also be used to persist/load payloads to/from the cloud!
LOGGER | `self.logger` | `Logger` | A logger

The best way to understand persistable is to see some examples.

# Examples
Some of these examples can be interactively tried by loading the corresponding jupyter notebooks in the `examples/`
folder.

## 1) Dataset Generation
The following shows a payload scalars drawn from a Gaussian distribution.

```python
from dataclasses import dataclass
from numpy.typing import NDArray
from pathlib import Path
from persistable import PersistableParams
from persistable import Persistable
from typing import Any

import numpy as np


@dataclass
class GaussianDistributedPointsParams(PersistableParams):
    """ Params for GaussianDistributedPointsP.

    Parameters:
        n (int): number of gaussian distributed points.
        random_state (int): random_state for generator.
    """

    n: int
    random_state: int = 100


class GaussianDistributedPointsP(Persistable[NDArray[np.float64], GaussianDistributedPointsParams]):
    """ Persistable payload of Gaussian distributed points.

    """

    def _generate_payload(self, **untracked_payload_params: Any) -> NDArray[np.float64]:
        np.random.seed(self.params.random_state)
        return np.random.random(self.params.n)


data_dir = Path('.').absolute() / "example-data"
params = GaussianDistributedPointsParams(n=100, random_state=10)
gaussian_distributed_points_p = GaussianDistributedPointsP(data_dir=data_dir, params=params, tracked_persistable_dependencies=None)
gaussian_distributed_points_p.generate() # Generate and persist the payload to storage
```

`>>> gaussian_points_p.payload[0]` gives `0.77132064`

In the future, this persisted payload (albeit simple) can be reloaded instead of recalculated.
```python
gaussian_distributed_points_p_2 = GaussianDistributedPointsP(data_dir=data_dir, params=params)
gaussian_distributed_points_p_2.load()
```

`>>> gaussian_points_p.payload[0]` gives `0.77132064`


---
In this example, a very simple persistable class with a numpy array payload was defined as follows:
1. Define parameters as dataclass inheriting from `PersistableParams`:
   ```python
   from dataclasses import dataclass
   from persistable import PersistableParams

   @dataclass
   class GaussianDistributedPointsParams(PersistableParams):
       ...
	```
2. Define persistable subclass, which requires at a minimum:
	1. a payload type (e.g. `NDArray`)
	2. a parameters type (e.g. `GaussianDistributedPointsParams`)
	3. a generate_payload function that returns the generated payload (e.g. here, some random distribution of points)
   ```python
   from persistable import Persistable
   from numpy.typing import NDArray

   import numpy as np

   class GaussianDistributedPointsP(Persistable[NDArray[np.float64], GaussianDistributedPointsParams]):
       def _generate_payload(self, **untracked_payload_params: Any) -> NDArray[np.float64]:
           np.random.seed(self.params.random_state)
           return np.random.random(self.params.n)
   ```


## 2) Simple Outlier Detection That Depends on Dataset Persistable
The following is an example of a outlier detection model, `OutlierEstimator`, made persistable, and generated based on
the `GaussianDistributedPointsP` persistable created in the example above.

```python
from dataclasses import dataclass
from persistable import Persistable, PersistableParams
from numpy.typing import NDArray
from pathlib import Path
from typing import Optional, Any

import numpy as np


@dataclass
class OutlierEstimatorParams(PersistableParams):
    """ Params for OutlierEstimator.

    Parameters:
        z_threshold (float): number of standard deviations from the mean for which to consider a point an outlier.
    """

    z_threshold: int


class OutlierEstimator:
    def __init__(self, z_threshold: float) -> None:
        self.z_threshold = z_threshold

        self._mean = Optional[float]
        self._stdev = Optional[float]

    def fit(self, data: NDArray[np.float64]) -> None:
        self._mean = np.mean(data)
        self._stdev = np.std(data)

    def transform(self, data: NDArray[np.float64]) -> NDArray[np.float64]:
        return np.abs((data - self._mean) / self._stdev) > self.z_threshold


class OutlierEstimatorP(Persistable[OutlierEstimator, OutlierEstimatorParams]):
    """ Persistable payload of Gaussian distributed points.

    """
    def __init__(
        self,
        data_dir: Path,
        params: OutlierEstimatorParams,
        *,
        data_points_p: GaussianDistributedPointsP,
    ) -> None:
        super().__init__(data_dir, params, verbose=True, tracked_persisable_dependencies=[data_points_p])
        self.data_points_p = data_points_p

    def _generate_payload(self, **untracked_payload_params: Any) -> OutlierEstimator:
        outlier_estimator = OutlierEstimator(z_threshold = self.params.z_threshold)
        outlier_estimator.fit(self.data_points_p.payload)

        return outlier_estimator
```
Just like in example one, parameters for the estimator are tracked via a `PersistableParams` object (here
`OutlierEstimatorParams`), and the persistable estimator `OutlierEstimatorP` has a generator_payload method that
depends on another persisable `GaussianDistributedPointsP`.

The only addition


# Conclusion
In general, the benefit to using `Persistable` is maximal when:
* payload generation is computationally expensive payload and would benefit by doing so only once
* it's important to keep track of pipeline parameters and versions and have results accessible later (i.e. persisted)

