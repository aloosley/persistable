from distutils.core import setup

setup(
    name='persistable',
    version='0.1.0',
    packages=['persistable'],
    url='',
    license='',
    author='Alex Loosley',
    author_email='a.loosley@reply.de',
    description='A general package for persisting and loading models with parameter tracking',
    install_requires=[
        "pandas>=0.20.3",
        "numpy>=1.13.1",
        "tqdm>=4.15.0",
        "toolz>=0.8.2",
        "cytoolz>=0.8.2",
        "wrapt>=1.10.11"
    ]
)