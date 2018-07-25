import os

from setuptools import find_packages, setup


project = 'passport'


def static_files(path, prefix):
    for root, _, files in os.walk(path):
        paths = []
        for item in files:
            paths.append(os.path.join(root, item))
        yield (root.replace(path, prefix), paths)


setup(
    name=project,
    version='2.4.1',
    url='https://passport.clayman.pro',
    license='MIT',
    author='Kirill Sumorokov',
    author_email='sumorokov.k@gmail.com',
    description='Auth service',

    packages=find_packages(exclude=['tests']),

    zip_safe=True,
    include_package_data=True,

    data_files=[item for item in static_files('%s/storage/sql' % project,
                                              'usr/share/%s' % project)],

    install_requires=[
        'aiodns==1.1.1',
        'aiohttp==3.3.2',
        'asyncpg==0.16.0',
        'cchardet==2.1.1',
        'cerberus==1.2',
        'click==6.7',
        'passlib==1.7.1',
        'prometheus_client>=0.0.19',
        'pyjwt==1.6.4',
        'pyyaml==4.2b4',
        'raven==6.9.0',
        'raven-aiohttp==0.7.0',
        'ujson==1.35',
        'uvloop==0.10.1',
    ],

    extras_require={
        'dev': [
            'flake8',
            'flake8-bugbear',
            'flake8-builtins-unleashed',
            'flake8-comprehensions',
            'flake8-import-order',
            'flake8-pytest',

            'pytest',
            'pytest-aiohttp',
            'pytest-postgres',
            'coverage',
            'coveralls'
        ]
    },

    entry_points='''
        [console_scripts]
        passport=passport.management.cli:cli
    '''
)
