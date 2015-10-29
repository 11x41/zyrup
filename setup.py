#!/usr/bin/env python2.7
"""
zyrup package
"""
from os import walk
from os.path import join as path_join
from setuptools import setup, find_packages


def readme():
    with open('README.md') as f:
        return f.read()


def data_dir(path):
    for dirpath, dirnames, filenames in walk(path):
        yield (dirpath, [path_join(dirpath, f) for f in filenames])

setup(
    name="zyrup",
    version='1.0.0',
    description='Zuora Python Library',
    long_description=readme(),
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: SOAP :: Zuora',
    ],
    keywords='zuora',
    url='https://github.com/mqarty/zyrup',
    author='Marty Berryman',
    author_email='me@mqarty.com',
    license='GPL',
    packages=['zyrup'],
    install_requires=[
        'suds ==0.3.9',
        'requests ==1.2.3',
        # 'gevent ==1.0.1',
    ],
    zip_safe=False,
    test_suite='nose.collector',
    tests_require=[
        'nose ==1.3.4',
        'mock ==1.0.1'
    ],
    data_files=[] + list(data_dir('config')),
)