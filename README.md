sless
=====
**less-like reader for structured log files**

![Usage animation](https://raw.githubusercontent.com/dpedu2/sless/master/sless.gif)

A tool for reading Strucuted Logs aka text files containing newline-separated json objects. Each object is presented as a single line and can be
expanded to show all attributes. Reading very large files is supported but large gzipped files do not work well.

Quick start
-----------

* Install: `python3 setup.py install`
* Run: `sless my_file.json`

Requirements
------------

Python 3 and `urwid` module.

Having the `ujson` module - a faster version of the native json module - is recommended but not required.

Customize
---------

Display different key in unexpanded previews: `-p` or `--preview-keys other,keys`


Roadmap
-------

* Filtering
* Exporting
* Performance improvements
