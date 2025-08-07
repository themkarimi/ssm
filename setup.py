#!/usr/bin/env python3

from setuptools import setup

setup(
    name="sealedsecret-manager",
    version="1.0.0",
    description="A streamlined CLI tool for Kubernetes SealedSecrets",
    author="MSC",
    py_modules=["ssm"],
    install_requires=[
        "PyYAML",
    ],
    entry_points={
        "console_scripts": [
            "ssm=ssm:main",
        ],
    },
    python_requires=">=3.7",
)
