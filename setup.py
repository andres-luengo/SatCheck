from setuptools import setup, find_packages

# Read the requirements from environment.yml dependencies
requirements = [
    "pandas",
    "numpy", 
    "pyephem",  # The pip package name for ephem
    "requests",
    "astropy",
    "matplotlib",
    "blimpy==2.0.11",
    "turbo-seti",  # Available on PyPI
    "pymysql",
    "google-cloud-bigquery[bqstorage,pandas]",
]

setup(
    name="satcheck",
    version="0.1.0",
    author="Breakthrough Listen",
    description="A package to look for satellites in Breakthrough Listen Data",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "findSats=satcheck.findSats:main",
            "genPlotsAll=satcheck.genPlotsAll:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Astronomy",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
    ],
)
