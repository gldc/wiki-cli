from setuptools import setup, find_packages

setup(
    name="wiki-cli",
    version="1.0.0",
    description="CLI harness for Wiki.js — manage pages, users, and content from the terminal",
    packages=find_packages(include=["wiki_cli", "wiki_cli.*"]),
    package_data={
        "wiki_cli": ["skills/*.md"],
    },
    install_requires=[
        "click>=8.0.0",
        "prompt-toolkit>=3.0.0",
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "wiki-cli=wiki_cli.wiki_cli:main",
        ],
    },
    python_requires=">=3.10",
)
