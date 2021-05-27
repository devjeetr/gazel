import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gazel",  # Replace with your own username
    version="0.0.3",
    author="Devjeet Roy",
    author_email="devjeetrr@gmail.com",
    description="Track fixations across edits for eyetracking experiments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/devjeetrr/pytrace",
    packages=setuptools.find_packages(),
    install_requires=[
        'pampy',
        'GitPython',
        'tqdm',
        'pandas',
        "tree_sitter",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8.5",
)
