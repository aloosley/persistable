from distutils.core import setup

setup(
    name='persistable',
    version='0.6.5',
    packages=['persistable', 'persistable/util'],
    url='https://github.com/DataReply/persistable',
    download_url='https://github.com/DataReply/persistable/archive/0.6.4.tar.gz',
    license='',
    author='Alex Loosley, Stephan Sahm',
    author_email='a.loosley@reply.de, s.sahm@reply.de',
    description='An inheritable superclass with logging, and tools for persisting and '
                'loading models with parameter tracking',
    keywords = ['persisting', 'models', 'pipeline'],
    install_requires=[
        "cytoolz>=0.8.2",
        "dill>=0.2.8",
        "pyparsing>=2.2.0",
        "tqdm>=4.20.0",
        "wrapt>=1.10.11"
    ],
    python_requires=">=3.6"
)
