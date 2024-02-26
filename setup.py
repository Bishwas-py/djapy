from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="djapy",
    version="0.1.7",
    description="Do not quit using Django just because of Django Rest Framework, Django is JSOMe",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Bishwas-py/djapy",
    py_modules=["djapy"],
    packages=find_packages(include=["djapy", "djapy.*"]),
    package_data={
        "djapy": ["templates/djapy/*.html"]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent"
    ],
    install_requires=[
        "Django",
        "pydantic",
    ]
)
