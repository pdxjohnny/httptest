#!/usr/bin/env python3
'''
setup.py: Upload httptest to PyPi
'''
import os
from setuptools import setup, find_packages

def contents(*a):
    '''
    Opens a file relative to this file
    '''
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), *a), 'rb') as filedesc:
        return filedesc.read().decode('utf-8')

# Get the version and README
VERSION = contents('httptest', 'version.py').split()[-1].replace('\'', '')
README = contents('README.rst')

setup(
    name='httptest',
    packages=find_packages(),
    version=VERSION,
    data_files=[('', ['LICENSE']), ],
    entry_points={},
    description='Add unit tests to your http clients',
    long_description=README,
    author='John Andersen',
    author_email='johnandersenpdx@gmail.com',
    url='https://github.com/pdxjohnny/httptest',
    download_url='https://github.com/pdxjohnny/httptest/tarball/%s' % VERSION,
    license='MIT',
    keywords=['unittesting', 'testing', 'http', 'api', 'test'],
    classifiers=[
        'Environment :: Console',
        'Operating System :: POSIX :: Linux',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Intended Audience :: Developers'
    ]
)
