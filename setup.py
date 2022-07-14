# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='asdl_tools',
    version='0.2.0',
    description='Tools used for experiments at ASDL',
    long_description=readme,
    author='Luis Paulo Morais Lima',
    author_email='luispauloml@gmail.com',
    url='https://github.com/luispauloml/asdl_tools',
    license=license,
    packages=find_packages(),
    install_requires=['numpy', 'scipy']
)
