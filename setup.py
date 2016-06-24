#!/usr/bin/env python3
from setuptools import setup
from sless import __version__

setup(name='sless',
      version=__version__,
      description='A less-like reader for structure log',
      url='http://github.com/dpedu2/sless',
      author='dpedu',
      author_email='dave@interana.com',
      packages=['sless'],
      entry_points={
          'console_scripts': [
              'sless = sless.reader:main',
          ]
      },
      install_requires=[
          'urwid==1.3.1',
      ],
      zip_safe=False)
