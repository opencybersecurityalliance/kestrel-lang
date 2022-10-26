=========
Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog`_.

Unreleased
==========

1.5.2 (2022-10-26)
==================

Added
-----

- Relative path support for environment variable starting with ``KESTREL`` #248
- Relative path support for path in ``LOAD``/``SAVE``
- Relative path support for local uri, i.e., ``file://xxx`` or ``file://./xxx`` in ``GET``
- Unit test on relative path in environment variable
- Unit test on relative path in LOAD
- Unit test on relative path in data source in GET

1.5.1 (2022-10-25)
==================

Added
-----

- Type checking in kestrel.semantics.reference
- New exception ``MissingDataSource``
- Unit test on variable reference in GET
- Unit test on last data source reuse

Fixed
-----

- Missing data source if not specified #257
- SymbolTable type error in code generation

Removed
-------

- Obsoleted exception ``UnsupportedStixSyntax``


1.5.0 (2022-10-24)
==================

Added
-----
- Introduce ExtendedCenteredGraphPattern (ECGP) for WHERE clause

    - Support optional SCO/entity type for centered graph (STIX compatible)
    - Support optional square brackets (STIX compatible)
    - Support Single or double quotes (STIX compatible)
    - Support nested list as value (STIX compatible)
    - Support Kestrel variable as reference
    - Support escaped characters in quoted value
    - Support ECGP to string/STIX/firepit transformation
    - Support ECGP pruning (centered or extended components)
    - Support ECGP merge/extend with another ECGP
    - Parse into STIX (now ECGP) #14
    - Normalize WHERE clause between GET and expression
    - Add WHERE clause to command FIND
    
- Upgrade arguments (in APPLY command)

    - Support quoted string in arguments #170
    - dereferring variables in arguments
    
- Upgrade path (in GET/APPLY/LOAD/SAVE command)

    - Support escaped characters in quoted datasrc/analytics/path
    
- Upgrade JSON parser for command NEW

- Upgrade operators in syntax to be case insensitive

- Upgrade timespan

    - absolute timespan without ``t`` and quotes
    - relative timespan for FIND
    
- Upgrade prefetch with WHERE clause to eliminate unnecessary query

- Multiple test cases for new syntax and features

- Add macOS (arm64) install requirement to documentation

Changed
-------
- Limit STIXPATH to ATTRIBUTE

    - command: SORT, GROUP, JOIN
    - expression clause: sort, attr

- Use explicit list like ``(1,2,3)`` or ``[1,2,3]`` for multi-value argument

- Formalize *semantics processor* in parser-semantics-codegen procedure

    - variable dereferencing in semantics processor
    - variable timerange extraction in semantics processor

1.4.2 (2022-09-26)
==================

Added
-----

- links to Black Hat 2022 website, recording, and demo/lab
- Kestrel logo in PNG
- link to the Kestrel binder service blog post

Fixed
-----

- consistent stix-shifter and connector versions

Changed
-------

- lowercase grammar strings

1.4.1 (2022-07-28)
==================

Added
-----

- multi-user cache folder support in debug mode #236
- ppid used in process identification (post-prefetch) #238
- process identification upgraded to a two-step approach
- fine-grained process identification time offsets
- per entity type prefetch config support #241
- support for automatically converting input files to STIX in stixbundle interface

Fixed
-----

- prefetch when parent_ref not in process table
- false positives in generic relation resolution
- second execution of a failed query should raise exception
- master runtime directory test case fix
- ``~`` support in config file path (env var)

1.4.0 (2022-05-16)
==================

Fixed
-----

- Fix NameError: name 'DataSourceError' is not defined
- Pass stix-shifter profile options into translation #230

Added
-----

- Relative timespans instead of START/STOP #181
  - e.g. ``LAST 5 MINUTES``
- Group by "binned" (or "bucketed") attributes
  - e.g. GROUP foo BY BIN(first_observed, 5m)

Changed
-------

- bump min Python version to 3.7
- update OCA slack invitation link

1.3.4 (2022-05-16)
==================

Fixed
-----

- broken /tmp/kestrel symbol link will crash a new session
- double close (double release resources) with context manager and aexit
- AttributeError with timestamped grouped variable #224
- subsequent GET would return no results #228

Added
-----

- documentation on macOS debug folder path
- interface figure updated with new planned interfaces
- dynamically load stix-shifter YAML profiles #227
- new exception: MissingEntityAttribute
- unit test: disp timestamped group by

Changed
-------

- codecov GitHub App enabled instead of codecov-bot
- stixshifter interface module ``connector`` split from ``interface``.

1.3.3 (2022-04-29)
==================

Fixed
-----

- Jupyter kernel crashing upon restart

1.3.2 (2022-04-22)
==================

Added
-----

- runtime warning generation for invalid entity type #200
- auto-complete relation in FIND
- auto-complete BY and variable in FIND
- add logo to readthedocs
- upgrade auto-complete keywords to be case sensitive #213
- add testing coverage into github workflows
- add codecov badge to README
- 31 unit tests for auto-completion
- the first unit test for JOIN
- two unit tests for ASSIGN
- five unit tests for EXPRESSION
- use tmp dir for generated testing data
- auto-deref with mixed ipv4/ipv6 in network-traffic

Fixed
-----

- missing ``_refs`` handling for 2 cases out of 4 #205
- incorrectly derefering attributes after GROUP BY
- incorrectly yielding variable when auto-completing relation in FIND
- pylint errors about undefined-variables

Changed
-------

- update grammar to separate commands yielding (or not) a variable
- change FUNCNAME from a terminal to an inlined rule
- differentiate the terminal "by"i between FIND and SORT/GROUP

1.3.1 (2022-04-16)
==================

Changed
-------

- GitHub Actions upgraded to setup-python@v3 + Python 3.10

Fixed
-----

- *The description failed to render* when uploading to PyPI.
- README.rst misses images when rendered at non-github sites, e.g., PyPI.

1.3.0 (2022-04-14)
==================

Added
-----

- internal data model upgraded to firepit 2.0.0 with full graph-like database schema:

  - new firepit data schema named `normalized <https://firepit.readthedocs.io/en/latest/database.html>`_.
  - the normalized schema extracts/recognizes entities/SCOs from STIX observations and stores them and their relations.
  - the normalized schema fully enables a Kestrel variable to refer to a list of homogeneous entities as a view in a relational-DB table.
  - older hunts will need to be re-executed.

- syntax upgrade: introducing the language construct *expression* to process a variable, e.g., adding a ``WHERE`` clause, and the processed variable can be

  - assigned to another variable, so one does not need another ``GET`` command with a STIX pattern to do filtering.
  - passed to ``DISP``, so ``DISP`` is naturally upgraded to support many clauses such as ``SORT``, ``LIMIT``, etc.

- new syntax for initial events handling besides entities:

  - entities in a variable do not have timestamps anymore; previously all observations of the entities were listed in a variable with timestamps.
  - use the function ``TIMESTAMPED()`` to wrap a variable into an expression when the user needs timestamps of the observations/events in which the entities appeared. This is useful for analyzing and visualizing events of entities through time, e.g., time series analysis of visited ``ipv4-addr`` entities in a variable.

- unit tests:

  - 5 more unit tests for command ``FIND``.
  - 2 more unit tests for command ``SAVE``.
  - 2 unit tests for expression ``TIMESTAMPED()``.

- new syntax added to language reference documentation
  
  - ``TIMESTAMPED``
  - ``DISP``
  - assign

- repo updates:

  - Kestrel logo created.
  - GOVERNANCE.rst including *versioning*, *release procedure*, *vulnerability disclosure*, and more.

Removed
-------

- the copy command is removed (replaced by the more generic assign command).

Changed
-------

- repo front-page restructured to make it shorter but providing more information/links.
- the overview page of Kestrel doc is turned into a directory of sections. The URL of the page is changed from `overview.html <https://kestrel.readthedocs.io/en/latest/overview.html>`_ to `overview <https://kestrel.readthedocs.io/en/latest/overview>`_.

1.2.3 (2022-03-23)
==================

Added
-----

- error message improvement: suggestion when a Python analytics is not found
- performance improvement: cache STIX bundle for any downloaded bundle in the stix-bundle data source interface
- performance improvement: pre-compile STIX pattern before matching in the stix-bundle data source interface
- performance improvement: skip prefetch when the generated prefetch STIX pattern is the same as the user-specified pattern
- documentation improvement: add building instructions for documentation
- documentation improvement: add data source setup under *Installation And Setup*
- documentation improvement: add analytics setup under *Installation And Setup*

Fixed
-----

- STIX bundle downloaded without ``Last-Modified`` field in response header #187
- case sensitive support for Python analytics profile name #189

1.2.2 (2022-03-02)
==================

Added
-----

- remote data store support
- unit test: Python analytics: APPLY after GET
- unit test: Python analytics: APPLY on multiple variables

Fixed
-----

- bump firepit version to fix transaction errors
- bug fix: verify_package_origin() takes 1 argument

Removed
-------

- unit test: Python 3.6 EOL and removed from GitHub Actions

1.2.1 (2022-02-24)
==================

Added
-----

- unit test: python analytics basic tests
- unit test: stix-shifter connector verification

Removed
-------

- dependency: matplotlib

1.2.0 (2022-02-10)
==================

Added
-----

- Kestrel main package

  - matplotlib figure support in Kestrel Display Objects
  - analytics interface upgraded with config shared to Kestrel
    
- Python analytics interface

  - minimal requirement design for writing a Python analytics
  - analytics function environment setup and destroy
  - support for a variety of display object outputs
  - parameters support
  - stack tracing for exception inside a Python analytics
    
- STIX-shifter data source interface

  - automatic STIX-shifter connector install
    
    - connector name guess
    - connector origin verification
    - comprehensive error and suggestion if automatic install failed
        
  - pretty print for exception inside a Docker analytics
    
- documentation

  - Python analytics interface
  - Kestrel debug page
  - flag to disable certificate verification in STIX-shifter profile example

Changed
-------

- abstract interface manager between datasource/analytics for code reuse

Fixed
-----

- auto-complete with data source #163
- exception for empty STIX-shifter profile
- STIX-shifter profile name should be case insensitive
- exception inappropriately caught when dereferencing vars with no time range

Removed
-------

- documentation about STIX-shifter connector install

1.1.7 (2022-01-27)
==================

Added
-----

- standalone Kestrel config module to support modular and simplified Kestrel config loading flow
- shareable-state of config between Kestrel session and any Kestrel data source interfaces
- stix-shifter interface upgraded with shareable-state of config support
- stix-shifter DEBUG level env var ``KESTREL_STIXSHIFTER_DEBUG``
- stix-shifter config/profile loading from disk ``~/.config/kestrel/stixshifter.yaml``
- debug message logging in ``kestrel_datasource_stixshifter``
- documentation for Kestrel main config with default config linked/shown

Changed
-------

- default Kestrel config not managed by ``pip`` any more
- turn main Kestrel from TOML into YAML ``~/.config/kestrel/kestrel.yaml``
- upgrade Kestrel data source interfaces API with new ``config`` parameter
- default stix-shifter debug level to INFO
- documentation upgrade for ``kestrel_datasource_stixshifter``

Fixed
-----

- Kestrel config upgrade inconsistency #116

1.1.6 (2021-12-15)
==================

Added
-----

- advanced code auto-completion with parser support

Fixed
-----

- dollar sign incorrectly display in Jupyter Notebook (dataframe to html)

Changed
-------

- installation documentation upgrade

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
