# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='waves',
    version='0.1.0',
    description='Simple 1D and 2D waves',
    long_description=readme,
    author='Luis Paulo Morais Lima',
    author_email='luispauloml@gmail.com',
    url='https://github.com/luispauloml/waves',
    license=license,
    packages=find_packages(),
    install_requires=['numpy']
)
