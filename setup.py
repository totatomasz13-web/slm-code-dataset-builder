#!/usr/bin/env python3
from setuptools import setup

setup(
    name="slm-code-dataset-builder",
    version="1.0.0",
    description="Pipeline do tworzenia datasetu do trenowania modeli LLM",
    py_modules=["run_pipeline"],
    install_requires=["requests"],
    entry_points={
        "console_scripts": [
            "slm-pipeline=run_pipeline:main",
        ],
    },
    python_requires=">=3.10",
)
