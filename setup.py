"""
Setup script for Tigris API Client
"""

from setuptools import setup, find_packages
import re

# from pytigris import __version__ as pytigris_version


_VERSION_RE = re.compile(r"__version__ = ['\"]([^'\"]+)['\"]")
_MODULE_BLACKLIST = {"setuptools", "wheel"}

setup(
    name="pytigris",
    version=_VERSION_RE.search(open("pytigris/__init__.py").read()).group(1),
    author="jupiterbjy",
    author_email="jupiterbjy@gmail.com",
    description="Unofficial Tigris API Client",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/jupiterbjy/pytigris",
    packages=find_packages(exclude=["tests"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[
        module
        for module in open("requirements.txt").read().splitlines()
        if module not in _MODULE_BLACKLIST
    ],
    extras_require={"trio": ["trio"]},
)
