from setuptools import setup

requires = [
    "pymongo",
]

packages = [
    'fwb',
    'fwb.persistence',
    'fwb.util',
    'fwb.cli',
]

setup(
    name="fwb",
    version="0.1.0",
    packages=packages,
    include_package_data=True,
    install_requires=requires,
    scripts=["scripts/fwb"],
    description="failwhale bots!"
)
