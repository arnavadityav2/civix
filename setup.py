from setuptools import setup, find_packages

setup(
    name="civix_ml",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "duckdb",
        "pandas",
        "pyarrow",
        "scikit-learn",
        "numpy",
        "xgboost",
        "tabulate",  # for .to_markdown()
    ],
)
