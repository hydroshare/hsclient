from setuptools import setup, find_packages

setup(
    name='hsclient',
    version='0.1',
    packages=find_packages(include=['hsclient', 'hsclient.*', 'hsclient.schemas.*', 'hsclient.schemas.rdf.*'],
                           exclude=("tests",)),
    install_requires=[
        'hsmodels',
        'requests',
        'pandas'
    ],
    url='https://github.com/hydroshare/hsclient',
    license='',
    author='Scott Black',
    author_email='scott.black@usu.edu',
    description='A python client for managing HydroShare resources'
)
