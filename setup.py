from setuptools import setup, find_packages

setup(
    name='hs_rdf',
    version='0.1',
    packages=find_packages(include=['hs_rdf', 'hs_rdf.*']),
    url='https://github.com/sblack-usu/hs_rdf',
    license='',
    author='Scott Black',
    author_email='scott.black@usu.edu',
    description='A python client for managing hydroshare resources'
)
