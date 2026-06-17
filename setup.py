from setuptools import find_packages, setup


setup(
    name="zhl-memory-core",
    version="0.2.3",
    description="Standalone NER and memory envelope core for ZHL robot memory.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="ZHL Technology",
    license="Proprietary",
    python_requires=">=3.10",
    packages=find_packages(include=["zhl_memory_core", "zhl_memory_core.*"]),
    install_requires=["cryptography>=42.0,<46.0"],
)
