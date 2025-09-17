#!/usr/bin/env python3
"""
Setup script for TACC Tools.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

# Read version from __init__.py
version = "0.1.0"
init_file = Path(__file__).parent / "tacc_tools" / "__init__.py"
if init_file.exists():
    with open(init_file) as f:
        for line in f:
            if line.startswith("__version__"):
                version = line.split("=")[1].strip().strip('"').strip("'")
                break

setup(
    name="tacc-tools",
    version=version,
    author="TACC Tools Contributors",
    author_email="support@tacc.utexas.edu",
    description="Helper utilities for Apptainer/Singularity ROS bag operations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    package_data={
        "tacc_tools": [
            "containers/*.def",
            "config/*.yaml",
            "scripts/*.py"
        ]
    },
    entry_points={
        "console_scripts": [
            "tacc-download-rosbag=tacc_tools.scripts.download_rosbag:main",
            "tacc-visualize-rosbag=tacc_tools.scripts.visualize_rosbag:main",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Robotics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
        "pandas>=1.3.0",
        "numpy>=1.20.0",
    ],
    extras_require={
        "ros1": [
            "rosbag",
            "rospkg",
        ],
        "ros2": [
            "rosbag2-py",
        ],
        "visualization": [
            "matplotlib>=3.3.0",
            "plotly>=5.0.0",
            "seaborn>=0.11.0",
        ],
        "remote": [
            "paramiko>=2.7.0",
            "scp>=0.13.0",
        ],
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.10",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ]
    },
    keywords="robotics ros rosbag singularity apptainer tacc hpc",
    project_urls={
        "Homepage": "https://github.com/artzha/tacc-tools",
        "Bug Reports": "https://github.com/artzha/tacc-tools/issues",
        "Source": "https://github.com/artzha/tacc-tools",
    },
)