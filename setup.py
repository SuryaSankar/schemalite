from setuptools import setup

setup(
    name='schemalite',
    version='0.1.23',
    description='A minimalistic Schema validation library',
    long_description='A minimalistic Schema validation library',
    packages=['schemalite'],
    include_package_data=True,
    license='MIT',
    install_requires=[
        "toolspy>=0.2.25"
    ],
    author='SuryaSankar',
    author_email='suryashankar.m@gmail.com')
