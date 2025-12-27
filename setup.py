# Author: Andres Espin
# Email: aaespin3@espe.edu.ec
# Role: Junior Developer
# Purpose: Independent Research Study

from setuptools import setup, find_packages

setup(
    name="orbitalskyshield",
    version="0.2.0",
    description="Satellite streak detection and orbital diffuse contribution estimation.",
    author="Andres Espin",
    author_email="aaespin3@espe.edu.ec",
    url="https://github.com/kiboki1234/ProyectoAstronomia",
    packages=find_packages(),
    install_requires=[
        "astropy>=5.0",
        "numpy>=1.20",
        "scipy>=1.7",
        "matplotlib>=3.5",
        "pyyaml>=6.0",
        "typer>=0.9",
        "scikit-image>=0.19",
        "pandas>=1.4",
    ],
    python_requires=">=3.9",
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=23.0",
            "ruff>=0.0.260",
            "mypy>=1.0",
        ]
    },
)
