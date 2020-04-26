import setuptools

with open("Readme.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="torrentds",
    version="0.0.1",
    author="Aron Radics",
    author_email="radics.aron.jozsef@gmail.com",
    description="Package to ",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/radaron/torrentds",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    install_requires=[
          #TODO
    ],
    python_requires='>=3.6',
)
