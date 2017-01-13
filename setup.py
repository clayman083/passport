from setuptools import find_packages, setup


setup(
    name='passport',
    version='0.1.0',
    url='https://passport.clayman.pro',
    license='MIT',
    author='Kirill Sumorokov',
    author_email='sumorokov.k@gmail.com',
    description='Auth service',

    packages=find_packages(exclude=['tests']),

    install_requires=[
        'aiohttp',
        'asyncpg',
        'cerberus',
        'click',
        'passlib',
        'pyjwt',
        'pyyaml',
        'ujson',
        'uvloop',
    ],

    extras_require={
        'develop': ['flake8'],
        # 'test': ['pytest', 'pytest-aiohttp', 'pytest-cov', 'pytest-postgres',
        #          'coverage', 'tox']
    },

    tests_require=[
        'pytest',
        'pytest-aiohttp',
        'pytest-cov',
        'pytest-postgres',
        'coverage',
        'tox'
    ],

    entry_points='''
        [console_scripts]
        passport=passport.management.cli:cli
    '''
)
