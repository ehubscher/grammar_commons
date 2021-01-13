from setuptools import setup, find_packages

setup(
    name='grammar_commons',
    version='0.0.1',
    packages=find_packages(),
    author='Jordan Hubscher',
    author_email='jordan.hubscher@gmail.com',
    description='Provides common utility functions and constants relevant to BNF grammars.',
    keywords='grammar commons utility library',
    project_urls={'Source Code': 'https://github.com/jhubscher/grammar_commons'},
    install_requires=['regex']
)
