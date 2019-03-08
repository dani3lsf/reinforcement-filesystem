# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='Armazenamento Adaptativo com Reinforcement Learning',
    version='0.0.1',
    description='Este projeto tem como objetivo desenvolver um sistema de armazenamento, baseado em FUSE, que utiliza técnicas de reinforcement learning para otimizar o seu desempenho e custo (por exemplo, ao utilizar diferentes serviços de armazenamento na nuvem) de forma completamente autónoma.',
    long_description=readme,
    author='projetolei1819',
    author_email='projetolei1819@gmail.com',
    url='https://github.com/helenapoleri/reinforcement-filesystem',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
