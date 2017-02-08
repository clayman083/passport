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

    zip_safe=True,
    include_package_data=True,

    install_requires=[
        'aiohttp',
        'alembic',
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
    },

    entry_points='''
        [console_scripts]
        passport=passport.management.cli:cli
    '''
)
