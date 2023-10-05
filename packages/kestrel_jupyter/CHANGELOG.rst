=========
Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog`_.

1.0.9 (2023-06-14)
==================

Changed
-------

- improved syntax highlighting

1.0.8 (2023-05-17)
==================

Changed
-------

- logging API update for ``kestrel-lang==1.6.0``

Removed
-------

- Python 3.7 support

1.0.7 (2022-12-08)
==================

Fixed
-----

- install broke with Jupyter ``notebook>=6.5``
- mitigate pip resolution issue #24
- codecov upload failed with multiple tests

Removed
-------

- ``pandas`` as explicit dependency (in ``kestrel-lang`` package already)

1.0.6 (2022-09-26)
==================

Added
-----

- Kestrel huntflow file extention (``.hf``) to support downloading a huntbook as a Kestrel huntflow for executing on the command line.

1.0.5 (2022-04-29)
==================

Fixed
-----

- Jupyter kernel crashing upon restart

1.0.4 (2022-04-22)
==================

Added
-----

- 2 initial unit tests
- GitHub workflows

  - unit testing
  - style checking
  - unimport checking

- code coverage accessment and badge
- README

  - link to CONTRIBUTING
  - link to GOVERNANCE

Fixed
-----

- Jupyter notebook kernel exit error #12

1.0.3 (2022-04-22)
==================

Added
-----

- DisplayWarning support

1.0.2 (2022-02-07)
==================

Added
-----

- Entire call stack in log if exception occurred.

Fixed
-----

- Jupyter Lab not display results #4

1.0.1 (2021-06-22)
==================

Fixed
-----

- Debug flag passing bug.

Added
-----

- Publishing-to-PyPI github workflow

1.0.0 (2021-05-18)
==================

Added
-----

- First release of Kestrel Jupyter.

.. _Keep a Changelog: https://keepachangelog.com/en/1.0.0/
