from setuptools import setup, find_packages

setup(
    name='medical_smolagent',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'smolagents',
        'langchain',
        'sentence-transformers',
        'loguru',
        'pydantic',
        'requests',
    ],
)    