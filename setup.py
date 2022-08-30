from distutils.core import setup
from typing import List

from setuptools import find_packages

long_description = (
    "Persistable is a lightweight framework that helps developers clearly define parametrized "
    "programmatic pipelines, and reproducibly generate, persist, and load artifacts using parameter "
    "based persisting and loading."
)

install_requires: List[str] = ["numpy>=1.21.0"]
dev_requires: List[str] = [
    "pre-commit>=2.19.0",
    "pytest>=7.1.2",
]

setup(
    name="persistable",
    version="1.2.1",
    packages=find_packages(),
    url="https://github.com/aloosley/persistable",
    download_url="https://github.com/aloosley/persistable/archive/1.2.1.tar.gz",
    license="",
    author="Alex Loosley, Stephan Sahm",
    author_email="aloosley@alumni.brown.edu, Stephan.Sahm@gmx.de",
    description="Reproducible parameter based pipelines and persisting",
    long_description=long_description,
    keywords=["persisting", "models", "pipeline"],
    install_requires=install_requires,
    extras_require=dict(dev=dev_requires),
    python_requires=">=3.9",
)
