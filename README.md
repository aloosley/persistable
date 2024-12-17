![](https://img.shields.io/badge/version-1.2.3-green.svg)
[![Build & Test](https://github.com/aloosley/persistable/actions/workflows/python-build.yml/badge.svg)](https://github.com/aloosley/persistable/actions/workflows/python-build.yml)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/dwyl/esta/issues)

<img src="logo.png" alt="Persistable - Programmatic Data Pipelines with Parameter Based Persisting and Loading">

# Introduction

Persistable is a lightweight framework that helps developers clearly define parametrized programmatic pipelines, and
reproducibly generate, persist, and load artifacts using parameter based persisting and loading.

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
The following shows a persistable payload of scalars drawn from a Gaussian distribution.  As with all persistables,
once the payload is generated, parameter based persistence allows it to be automatically reloaded when regeneration is
unwanted.

```python
from dataclasses import dataclass
from numpy.typing import NDArray
from pathlib import Path
from persistable import PersistableParams
from persistable import Persistable
from persistable.exceptions import InvalidPayloadError
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

    def _validate_payload(self, payload: NDArray[np.float64]) -> None:
        if not isinstance(payload, np.ndarray):
            raise TypeError("Payload must be of type np.ndarray to be valid.")
        if not payload.ndim == 2:
            raise InvalidPayloadError("Payload must be a 1-D array.")
        if len_ := len(payload) != self.params.n:
            raise InvalidPayloadError(f"Payload expected to have length {self.params.n} (len(payload)={len_})")

# Generate persistable (and save it to example-data directory)
data_dir = Path('.').absolute() / "example-data"
params = GaussianDistributedPointsParams(n=100, random_state=10)
gaussian_distributed_points_p = GaussianDistributedPointsP(
   data_dir=data_dir, params=params, tracked_persistable_dependencies=None
)
gaussian_distributed_points_p.generate() # Generate and persist the payload to storage
# >>> gaussian_distributed_points_p.payload[0]
# >>> 0.77132064

# Parameter based reload without regeneration
gaussian_distributed_points_reloaded_p = GaussianDistributedPointsP(
   data_dir=data_dir, params=params, tracked_persistable_dependencies=None
)
gaussian_distributed_points_reloaded_p.load()
# >>> gaussian_distributed_points_reloaded_p.payload[0]
# >>> 0.77132064
```

---
In this example, a very simple persistable class carrying a numpy array payload was defined as follows:
1. Define persistable parameters for generating Gaussian distributed points by implementing a `PersistableParams` dataclass:
   ```python
   from dataclasses import dataclass
   from persistable import PersistableParams

   @dataclass
   class GaussianDistributedPointsParams(PersistableParams):
       ...
    ```
2. Implement the Gaussian distributed points Persistable subclass, which requires:
    1. a payload type (e.g. `NDArray`)
    2. a parameters type (e.g. `GaussianDistributedPointsParams`)
    3. a generate_payload function that returns the generated payload (e.g. here, some random distribution of points)

   In this example, a payload validator was also implemented by overriding `_validate_payload`.
   ```python
   from persistable import Persistable
   from persistable.exceptions import InvalidPayloadError
   from numpy.typing import NDArray
   from typing import Any

   import numpy as np

   class GaussianDistributedPointsP(Persistable[NDArray[np.float64], GaussianDistributedPointsParams]):
       def _generate_payload(self, **untracked_payload_params: Any) -> NDArray[np.float64]:
           np.random.seed(self.params.random_state)
           return np.random.random(self.params.n)

       def _validate_payload(self, payload: NDArray[np.float64]) -> None:
           if not isinstance(payload, np.ndarray):
               raise TypeError("Payload must be of type np.ndarray to be valid.")
           if not payload.ndim == 2:
               raise InvalidPayloadError("Payload must be a 1-D array.")
           if len_ := len(payload) != self.params.n:
               raise InvalidPayloadError(f"Payload expected to have length {self.params.n} (len(payload)={len_})")
   ```

3. Instantiate the persistable object to track a particular `data_dir` and use an instance of
   `GaussianDistributedPointsParams` for parameter based persisting and loading.  Note,
   `tracked_persistable_dependencies=None` indicates that there are no persistable dependencies for
   generating this payload (for on this in example two)
   ```python
   data_dir = Path('.').absolute() / "example-data"
   params = GaussianDistributedPointsParams(n=100, random_state=10)
   gaussian_distributed_points_p = GaussianDistributedPointsP(
       data_dir=data_dir, params=params, tracked_persistable_dependencies=None
   )
   gaussian_distributed_points_p.generate() # Generate and persist the payload to storage
   ```

   `>>> gaussian_distributed_points_p.payload[0]` gives `0.77132064`

   The generate method persists the generated payload by default under the folder defined by `data_dir`.  Note, log
   files and humanly readable parameter json files (making it more easy to share artifacts with others) are also
   persisted.  In the future, persistable can automatically look in the `data_dir` to determine if the payload can
   be loaded without needing to be recalculated (good for payloads that need a lot of compute to calculate).

   ```python
   gaussian_distributed_points_reloaded_p = GaussianDistributedPointsP(
       data_dir=data_dir, params=params, tracked_persistable_dependencies=None
   )
   gaussian_distributed_points_reloaded_p.load_generate()
   ```

   `>>> gaussian_distributed_points_reloaded_p.payload[0]` gives `0.77132064`

   The `.load_generate()` method first tries to load from the `data_dir`, and falls back to generating the payload if
   it has not been previously persisted.  There is also a `.load()` method when there should be no fallback for loading.

   Note to that persisting and loading is done using a default file-io object that pickles payloads.  Developers can
   also inject their own custom file-io object that persists/loads payloads to/from specific places
   (i.e. local, cloud storage, sftp, etc.) and/or with defined formats (i.e. pickle, csv, avro, etc.)

## 2) Simple Outlier Detection (with tracked persistable dependency on Dataset)
The following is an example of a outlier detection model, `OutlierEstimator`, made persistable, and generated based on
the `GaussianDistributedPointsP` persistable created in the example above.  Since outlier estimators with equivalent
(hyper-)parameters are will be different depending on the data, we want to track the dataset parameters when doing
parameter based persisting and loading.  This example shows how to do that.

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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}{self.__dict__}"


class OutlierEstimatorP(Persistable[OutlierEstimator, OutlierEstimatorParams]):
    """ Persistable outlier estimator dependent on persistable dataset of type GaussianDistributedPointsP.

    """
    def __init__(
        self,
        data_dir: Path,
        params: OutlierEstimatorParams,
        *,
        data_points_p: GaussianDistributedPointsP,
    ) -> None:
        super().__init__(data_dir, params, tracked_persistable_dependencies=[data_points_p], verbose=True)
        self.data_points_p = data_points_p

    def _generate_payload(self, **untracked_payload_params: Any) -> OutlierEstimator:
        outlier_estimator = OutlierEstimator(z_threshold = self.params.z_threshold)
        outlier_estimator.fit(self.data_points_p.payload)

        return outlier_estimator


data_dir = Path('.').absolute() / "example-data"
params = OutlierEstimatorParams(z_threshold=2)
outlier_estimator_p = OutlierEstimatorP(data_dir=data_dir, params=params, data_points_p=gaussian_distributed_points_p)
outlier_estimator_p.load_generate()
# >>> outlier_estimator_p.payload
# >>> OutlierEstimator{'z_threshold': 2, '_mean': 0.48534879111973994, '_stdev': 0.27497659243084727}
```

Just like in example one, the generation is defined by `_generate_payload`.  The parameters for generation
and parameter based persisting and loading are defined by a subclass of `PersistableParams` called
`OutlierEstimatorParams` **and** the `tracked_persistable_dependencies`, which in this case in the instance of
`GaussianDistributedPointsP`.  Thus, the outlier estimator is uniquely defined by it's hyperparameters and the data
used to train it.

# Conclusion
In general, the benefit to using `Persistable` is maximal when:
* payload generation is computationally expensive payload and would benefit by doing so only once
* it's important to keep track of pipeline parameters and versions and have results accessible later (i.e. persisted)

