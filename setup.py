import setuptools


with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="tinylock_py",
    description="Tinylock Python SDK",
    author="Tinylock",
    author_email="contact@tinylock.org",
    version="2.0.0",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    project_urls={
        "Source": "https://github.com/tinylock-org/tinylock_py",
    },
    install_requires=[
        "py-algorand-sdk >= 1.6.0",
        "pyteal >= 0.9.0",
        "tinyman-py-sdk >= 0.0.4"
        ],
    packages=setuptools.find_packages(where="."),
    python_requires=">=3.7"
)
