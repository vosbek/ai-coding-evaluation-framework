"""
Setup script for AI Coding Assistant Evaluation Framework.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-coding-evaluation-framework",
    version="0.1.0",
    author="AI Evaluation Team",
    description="A comprehensive framework for evaluating AI coding assistants",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.108.0",
        "uvicorn>=0.25.0",
        "sqlalchemy>=2.0.25",
        "pydantic>=2.5.3",
        "python-dotenv>=1.0.0",
        "alembic>=1.13.1",
        "watchdog>=3.0.0",
        "pandas>=2.1.4",
        "matplotlib>=3.8.2",
        "seaborn>=0.13.0",
        "jinja2>=3.1.2",
        "click>=8.1.7",
        "rich>=13.7.0",
        "structlog>=23.2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.4",
            "pytest-asyncio>=0.23.2",
            "black>=23.12.1",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "eval-framework=src.logging.cli:cli",
        ],
    },
)