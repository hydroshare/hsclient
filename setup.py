from setuptools import setup

setup(
    name='hs_rdf',
    version='0.1',
    packages=['hs_rdf', 'hs_rdf.implementations', 'hs_rdf.implementations.hydroshare', hs_rdf.schemas', 'hs_rdf.namespaces'],
    url='https://github.com/sblack-usu/hs_rdf',
    license='',
    author='Scott Black',
    author_email='scott.black@usu.edu',
    description='A python client for managing hydroshare resources'
)
