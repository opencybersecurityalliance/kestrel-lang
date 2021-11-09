=========
Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog`_.

1.1.5 (2021-11-08)
==================

Changed
-------

- dependency version bump for the open hunting stack (Black Hat Europe 2021)
- installation documentation updates

1.1.4 (2021-10-27)
==================

Added
-----

- multi-data source support
- detailed error message from stix-shifter

Fixed
-----

- Limit Python<=3.9 since numpy is not ready for 3.10

1.1.3 (2021-10-08)
==================

Added
-----

- GROUP BY multiple attributes
- Aggregation function in GROUP BY
- Support alias in GROUP BY
- New test cases for GROUP BY
- Documentation update for GROUP BY

1.1.2 (2021-09-13)
==================

Fixed
-----

- Aggregated entity recognition in a variable after command GROUP

1.1.1 (2021-09-03)
==================

Added
-----

- Minimal dependent package versions #67
- Configration option to disable execution summary display #86
- Auto-removal of obsolete session caches #34
- SQLite requirement in installation documentation

Fixed
-----

- Python 3.6 support on command line utility #97

Changed
-------

- Adjusting logging message levels to avoid confusion

1.1.0 (2021-08-18)
===================

Added
-----

- firepit API upgrade to support aggregated entities
- Integer/float support as JSON value in command NEW

Changed
-------

- Documentation update on command SORT/GROUP regarding aggregated entities

1.0.14 (2021-08-18)
===================

Changed
-------

- firepit version specification before API updates

1.0.13 (2021-08-13)
===================

Fixed
-----

- Single quotes support in STIX patterns to fix #95
- Variable summary deduplication

Added
-----

- Expected components in syntax error messages

1.0.12 (2021-08-03)
===================

Fixed
-----

- Display formatting of exceptions

1.0.11 (2021-08-03)
===================

Fixed
-----

- NaN to None in loading data
- Catch InvalidAttr in summary.py

Added
-----

- InvalidAnalyticsInput exception 
- MacOS with Python 3.9 testing environment
- RSA link to README

1.0.10 (2021-07-19)
===================

Fixed
-----

- Missing log in command line mode #84
- Typo in documentation

Added
-----

- Select config file via environment variable #82

1.0.9 (2021-07-07)
==================

Added
-----

- Full default datasource/analytics schema support
- Initial install-in-docker support #54

1.0.8 (2021-07-01)
==================

Changed
-------

- Command fix in documentation
- VarStruct init with pre-calculated parameters

1.0.7 (2021-06-29)
==================

Changed
-------

- Documentation grammar and style improvements

Added
-----

- Syntax sugar: omitted schema inference (data source and analytics) if only one schema
- Temporary store view removal if not in debug mode #63

1.0.6 (2021-06-24)
==================

Fixed
-----

- Config override bug
- STIX bundle data source bug with HTTP/HTTPS
- GROUP BY error without id #43
- Cannot execute all-comment code block #50
- Inappropriate error for non-existence relation #51

Changed
-------

- Improved ``.gitignore``
- Comprehensive process entity recognition #53
- Updated parameter handling in docker analytics interface #49

1.0.5 (2021-06-10)
==================

Fixed
-----

- Command FIND with network-traffic return gives exception #44

Added
-----

- Debug flag from environment variable
- Hunting GIF in README

1.0.4 (2021-06-08)
==================

Added
-----

- GitHub action for pull requests
    - Unit testing
    - Code style check
    - Unused imports check
- GitHub issue templates

Changed
-------

- More comprehensive entity identification logic
- Use firepit.merge() to implement prefetch merge
- Typo fix in doc

1.0.3 (2021-05-31)
==================

Fixed
-----

- Fix the timestamp parsing issue #6
- Fix version: https://github.com/pypa/pypi-support/issues/214

Added
-----

- Add proper exception to non-existent variable #8
- Add three issue templates #10
- Add GitHub Action to publish to Pypi

1.0.0 (2021-05-18)
==================

Added
-----

- First release of Kestrel Core.

.. _Keep a Changelog: https://keepachangelog.com/en/1.0.0/
