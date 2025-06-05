from setuptools import setup, find_packages

setup(
    name="macro-manager",
    version="0.1.0",
    description="Daily Macro Dashboard",
    author="",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "streamlit>=1.45",
        "pyyaml>=6.0",
        "matplotlib>=3.10",
    ],
    entry_points={
        "console_scripts": [
            "macro-manager=macro_manager.__main__:main",
        ]
    },
    include_package_data=True,
)
