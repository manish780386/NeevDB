"""
NeevDB - PyPI Package Setup
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="neevdb",
    version="2.0.0",
    author="Manish Dange",
    description="A lightweight file-based database engine built with pure Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/manish780386/NeevDB.git",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Database",
        "Topic :: Database :: Database Engines/Servers",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "neevdb=cli:main",
        ],
    },
)