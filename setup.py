from distutils.core import setup
from typing import List

from setuptools import find_packages

install_requires: List[str] = ["numpy>=1.21.0"]
dev_requires: List[str] = [
    "pre-commit>=2.19.0",
    "pytest>=7.1.2",
]

setup(
    name="persistable",
    version="1.0.0",
    packages=find_packages(),
    url="https://github.com/aloosley/persistable",
    download_url="https://github.com/aloosley/persistable/archive/1.0.0.tar.gz",
    license="",
    author="Alex Loosley, Stephan Sahm",
    author_email="aloosley@alumni.brown.edu",
    description="An inheritable superclass with logging, and tools for persisting and "
    "loading models with parameter tracking",
    keywords=["persisting", "models", "pipeline"],
    install_requires=install_requires,
    extras_require=dict(dev=dev_requires),
    python_requires=">=3.9",
)
