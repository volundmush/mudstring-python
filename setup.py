import os
from setuptools import setup

os.chdir(os.path.dirname(os.path.realpath(__file__)))

OS_WINDOWS = os.name == "nt"


def get_requirements():
    """
    To update the requirements for MudTelnet, edit the requirements.txt file.
    """
    with open("requirements.txt", "r") as f:
        req_lines = f.readlines()
    reqs = []
    for line in req_lines:
        # Avoid adding comments.
        line = line.split("#")[0].strip()
        if line:
            reqs.append(line)
    return reqs

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# setup the package
setup(
    name="mudstring",
    version="0.5.0",
    author="Volund",
    maintainer="Volund",
    url="https://github.com/volundmush/mudstring-python",
    description="Simple monkey-patching library to make for amazing ANSI experiences in MUDs",
    license="MIT",
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=["mudstring"],
   # install_requires=get_requirements(),
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.5",
        "Intended Audience :: Developers",
        "Topic :: Games/Entertainment :: Multi-User Dungeons (MUD)",
        "Topic :: Games/Entertainment :: Puzzle Games",
        "Topic :: Games/Entertainment :: Role-Playing",
        "Topic :: Games/Entertainment :: Simulation",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    python_requires=">=3.5",
    project_urls={
        "Source": "https://github.com/volundmush/mudstring-python",
        "Issue tracker": "https://github.com/volundmush/mudstring-python/issues",
        "Patreon": "https://www.patreon.com/volund",
    },
)
