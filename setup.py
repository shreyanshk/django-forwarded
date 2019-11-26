import setuptools
import subprocess

with open("README.md", "r") as fh:
    long_description = fh.read()

version = subprocess.check_output(["git", "describe", "--tags"]).decode()[:-1]

setuptools.setup(
    name="Django-Forwarded",
    version=version,
    license='Apache License 2.0',
    author="Shreyansh Khajanchi",
    author_email="shreyansh.khajanchi@cern.ch",
    description='Support HTTP "Forwarded" header in your Django applications',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://gitlab.cern.ch/skhajanc/django-forwarded",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.6",
    install_requires=["django>=2.2", ],
    zip_safe=False,
    py_modules=['django_forwarded', ],
    platform='any',
)
