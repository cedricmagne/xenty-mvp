from setuptools import setup, find_packages

setup(
    name="xenty",
    version="0.1.0",
    packages=find_packages(),
    description="Twitter engagement analysis and prediction",
    author="Cedric Magne",
    python_requires=">=3.7",
    install_requires=[
        "numpy>=2.1.3",
        "pandas>=2.3.0",
        "scikit-learn>=1.7.0",
        "matplotlib>=3.10.3",
        "seaborn>=0.13.2",
        "plotly>=6.2.0",
        "tensorflow>=2.19.0",
        "streamlit>=1.46.1",
        "kagglehub>=0.3.12",
        "kaggle>=1.7.4.5",
        "nbformat>=5.10.4",
        "nbconvert>=7.16.6",
        "python-dotenv>=1.1.0",
    ],
)
