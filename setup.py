import os
import sys
import re
import ast
from subprocess import call
from itertools import chain
import io
import pip

try:
    from pip.req import parse_requirements
except ImportError:
    # The req module has been moved to pip._internal in the 10 release.
    from pip._internal.req import parse_requirements
try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install


ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
_version_re = re.compile(r"__version__\s+=\s+(.*)")

with open("owtf/__init__.py", "rb") as f:
    version = str(ast.literal_eval(_version_re.search(f.read().decode("utf-8")).group(1)))


def parse_file(filename, encoding="utf-8"):
    """Return contents of the given file using the given encoding."""
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)
    with io.open(path, encoding=encoding) as fo:
        contents = fo.read()
    return contents


links = []
requires = []

# new versions of pip requires a session
base_req = parse_requirements("requirements/base.txt", session=False)
docs_req = parse_requirements("requirements/docs.txt", session=False)
test_req = parse_requirements("requirements/test.txt", session=False)

requirements = chain(base_req, docs_req, test_req)

for item in requirements:
    if getattr(item, "url", None):  # older pip has url
        links.append(str(item.url))
    if getattr(item, "link", None):  # newer pip has link
        links.append(str(item.link))
    if item.req:
        requires.append(str(item.req))  # always the package name

post_script = os.path.join(ROOT_DIR, "scripts/install.sh")


class PostDevelopCommand(develop):
    """Post-installation for development mode."""

    def run(self):
        develop.run(self)
        print("Running post install")
        call(["/bin/bash", post_script])


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        # Need because of a setuptools bug: https://github.com/pypa/setuptools/issues/456
        self.do_egg_install()
        print("Running post install")
        call(["/bin/bash", post_script])


if sys.version_info < (2, 7, 9):
    # SSL connection fixes for Python 2.7
    requires.extend(["ndg-httpsclient", "pyasn1"])

if sys.version_info > (3, 0, 0):
    requires.extend(["black", "pre-commit"])

setup(
    name="owtf",
    version=version,
    url="https://github.com/owtf/owtf",
    license="BSD",
    author="Abraham Aranguren",
    author_email="abraham.aranguren@owasp.org",
    description="OWASP+PTES focused try to unite great tools and make pen testing more efficient",
    long_description=parse_file("README.md"),
    packages=find_packages(exclude=["node_modules", "node_modules.*"]),
    include_package_data=True,
    zip_safe=False,
    platforms="any",
    install_requires=sorted(requires, key=lambda s: s.split("==")[0].lower()),
    dependency_links=links,
    cmdclass={"develop": PostDevelopCommand, "install": PostInstallCommand},
    scripts=["bin/owtf"],
    entry_points={"console_scripts": ["owtf=owtf.core:main"]},
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Operating System :: POSIX :: Linux",
        "Topic :: Security",
    ],
)
