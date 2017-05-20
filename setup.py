from setuptools import find_packages, setup

entry_points = {
    'console_scripts': [
        'scrape_parks = campin.cli:scrape_parks',
        'scrape_reservations = campin.cli:scrape_reservations',
        'scrape_sites = campin.cli:scrape_sites',
    ],
    'paste.app_factory': [
        'main = campin.api:main',
    ]
}

install_requires = [
    'scrapy',
    'txpostgres',
    'python-dateutil',
    'aiopyramid',
    'asyncpg',
    'googlemaps',
    # Switch to aiopg and pyscopg2 if using pypy
    #'pyscopg2-cffi',
    #'aiopg',
    'formencode',
    'pillow',
]

dev_requires = [
    'pyramid_debugtoolbar'
]

setup(
    name='campin',
    version='1.0.0',
    description='',
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    extras_require={
        'dev': dev_requires,
    },
    entry_points=entry_points,
)
