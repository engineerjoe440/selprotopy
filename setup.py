# Import Necessary Files
import setuptools
import re

# Load Description Document
with open("README.md", "r") as fh:
    long_description = fh.read()

# Gather Version Information from Python File
with open("selprotopy/__init__.py", encoding="utf-8") as fh:
    file_str = fh.read()
    name = re.search('_name_ = \"(.*)\"', file_str).group(1)
    ver = re.search('_version_ = \"(.*)\"', file_str).group(1)
    # Version Breakdown:
    # MAJOR CHANGE . MINOR CHANGE . MICRO CHANGE
    print("Setup for:",name,"   Version:",ver)

# Generate Setup Tools Argument
setuptools.setup(
    name=name,
    version=ver,
    author="Joe Stanley",
    author_email="joe_stanley@selinc.com",
    description="Schweitzer Engineering Laboratories (SEL) Protocol Bindings in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/engineerjoe440/selprotopy",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    project_urls={
        "Source Repository": "https://github.com/engineerjoe440/selprotopy",
        "Bug Tracker": "https://github.com/engineerjoe440/selprotopy/issues",
        "Documentation": "https://engineerjoe440.github.io/selprotopy/",
        }
)