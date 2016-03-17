#!/usr/bin/env python

"Setuptools params"

from setuptools import setup, find_packages

VERSION = '0.1a'

modname = distname = 'ipmininet'

setup(
    name=distname,
    version=VERSION,
    description='A mininet extension providing components to emulate IP networks',
    author='Olivier Tilmans',
    author_email='olivier.tilmans@uclouvain.be',
    packages=find_packages(),
    include_package_data = True,
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Topic :: System :: Networking",
        ],
    keywords='networking OSPF IP mininet',
    license='GPLv2',
    install_requires=[
        'setuptools',
        'mako',
        'py2-ipaddress'
    ],
    tests_require=['pytest'],
    setup_requires=['pytest-runner']
)
