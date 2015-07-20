import os
from setuptools import setup

long_desc = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

setup(
    name = "GSim",
    version = "0.21",
    author = "Peter Rogers",
    author_email = "peter.rogers@gmail.com",
    url = "https://github.com/parogers/gsim",
    description = "G-Code simulator",
    license = "GPLv2+",
    packages=['gsim'],
    entry_points={'gui_scripts': ['gsim = gsim.main:main']},
    long_description=long_desc,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Manufacturing',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering',
    ],
)

