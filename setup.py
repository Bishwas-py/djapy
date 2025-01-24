from setuptools import setup, find_packages

with open("README.md", "r") as fh:
   long_description = fh.read()

setup(
   name="djapy",
   version="0.2.0.dev1",
   description="Fast, zero-boilerplate Django REST API framework with pure Python typing!",
   long_description=long_description,
   long_description_content_type="text/markdown",
   url="https://github.com/Bishwas-py/djapy",
   py_modules=["djapy"],
   packages=find_packages(include=["djapy", "djapy.*"]),
   package_data={
      "djapy": ["templates/djapy/*.html"]
   },
   project_urls={
      "Documentation": "https://djapy.io",
   },
   classifiers=[
      "Programming Language :: Python :: 3",
      "Programming Language :: Python :: 3.10",
      "Programming Language :: Python :: 3.11",
      "Programming Language :: Python :: 3.12",
      "Programming Language :: Python :: 3.13",
      "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
      "Operating System :: OS Independent"
   ],
   install_requires=[
      "Django",
      "pydantic",
   ],
   python_requires='>=3.10',
)
