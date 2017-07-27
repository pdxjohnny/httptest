#!/usr/bin/env python3
import os
from setuptools import setup, find_packages

# Get the version
with open(os.path.join('httptest', 'version.py'), 'rb') as fd:
    VERSION = fd.read().decode('utf-8').split()[-1].replace('\'', '')

setup(
    name='httptest',
    packages=find_packages(),
    version=VERSION,
    data_files=[('', ['LICENSE']), ],
    entry_points={},
    description='Add unit tests to your http clients',
    author='John Andersen',
    author_email='johnandersenpdx@gmail.com',
    url='https://github.com/pdxjohnny/httptest',
    download_url='https://github.com/pdxjohnny/httptest/tarball/%s' % VERSION,
    license='MIT',
    keywords=['unittesting', 'testing', 'http', 'api', 'test'],
    classifiers=[
        'Environment :: Console',
        'Operating System :: POSIX :: Linux',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.5',
        'Intended Audience :: Developers'
    ]
)
