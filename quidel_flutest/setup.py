from setuptools import setup
from setuptools import find_packages

required = [
    "numpy",
    "pandas",
    "pytest",
    "pytest-cov",
    "pylint",
    "delphi-utils",
    "imap-tools",
    "xlrd"
]

setup(
    name="quidel_flutest",
    version="0.1.0",
    description="Indicators Pulled from datadrop email",
    author="",
    author_email="",
    url="https://github.com/cmu-delphi/covidcast-indicators",
    install_requires=required,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.7",
    ],
    packages=find_packages(),
)