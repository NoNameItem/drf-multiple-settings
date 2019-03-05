import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="drf-multiple-settings",
    version="1.0.1",
    author="Artem Vasin",
    author_email="nonameitem@me.com",
    description="DRF ViewSets supporting different settings for actions",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'djangorestframework>=3.0'
    ],
)
