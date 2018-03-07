from distutils.core import setup

setup(
    name='persistable',
    version='0.3.3',
    packages=['persistable', 'persistable/util'],
    url='https://github.com/DataReply/persistable',
    download_url='https://github.com/DataReply/persistable/archive/0.3.3.tar.gz',
    license='',
    author='Alex Loosley',
    author_email='a.loosley@reply.de',
    description='An inheritable superclass with logging, and tools for persisting and '
                'loading models with parameter tracking',
    keywords = ['persisting', 'models', 'pipeline'],
    install_requires=[
        "cytoolz>=0.8.2",
        "wrapt>=1.10.11"
    ]
)
