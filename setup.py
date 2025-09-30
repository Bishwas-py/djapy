from setuptools import setup, find_packages

with open("README.md", "r") as fh:
   long_description = fh.read()

setup(
   name="djapy",
   version="0.3.1.dev0",
   description="Fast, zero-boilerplate Django REST API framework with pure Python typing!",
   long_description=long_description,
   long_description_content_type="text/markdown",
   url="https://github.com/Bishwas-py/djapy",
   package_dir={"": "src"},
   packages=find_packages(where="src", include=["djapy", "djapy.*"]),
   package_data={
      "djapy": ["templates/djapy/*.html", "py.typed"]
   },
   project_urls={
      "Documentation": "https://djapy.io",
   },
   classifiers=[
      "Development Status :: 4 - Beta",
      "Programming Language :: Python :: 3",
      "Programming Language :: Python :: 3.10",
      "Programming Language :: Python :: 3.11",
      "Programming Language :: Python :: 3.12",
      "Programming Language :: Python :: 3.13",
      "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
      "Operating System :: OS Independent",
      "Framework :: Django",
      "Framework :: Django :: 3.2",
      "Framework :: Django :: 4.0",
      "Framework :: Django :: 4.1",
      "Framework :: Django :: 4.2",
      "Framework :: Django :: 5.0",
      "Intended Audience :: Developers",
      "Topic :: Software Development :: Libraries :: Python Modules",
   ],
   install_requires=[
      "Django",
      "pydantic",
   ],
   python_requires='>=3.10',
)
