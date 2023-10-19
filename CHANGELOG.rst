=========
Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog`_.

1.8.0 (2023-10-18)
==================

Added
-----

- Hide credentials in debug log
- Type checking in kestrel/utils.py
- Merge ``opencybersecurityalliance/kestrel-jupyter`` repo into this repo as the umbralla package for Kestrel

Changed
-------

- Package name from ``kestrel-lang`` to ``kestrel-core`` to peel off components into standalone packages
- Establish two standalone datasource interface packages
- Establish two standalone analytics interface packages
- Update installation documentation

1.7.6 (2023-09-25)
==================

Added
-----

- ``DESCRIBE`` command to get insight of attributes
- ``ikestrel`` interactive shell (command-line utility)
- Custom stix-shifter connector support #402

Fixed
-----

- Command-line utility tests failed without install

1.7.5 (2023-09-07)
==================

Added
-----

- Kestrel Docker container image in DockerHub
- Documentation on how to use Kestrel Docker container
- case insensitive option ``(?i)`` for Elasticserach via stix-shifter data source interface (stix-shifter v6.2.1)

1.7.4 (2023-08-03)
==================

Added
-----

- New simpler default STIX patterns for stix-shifter-diag
- Connector verification/install in stix-shifter-diag #388
- Custom pattern (string and file) support for stix-shifter-diag
- Debug info output support for stix-shifter-diag
- Current time as stop time support for default pattern in stix-shifter-diag
- Query-translate-only mode for stix-shifter-diag

Changed
-------

- Fix/change the order of LIMIT and timespan in Lark file according to Kestrel doc
- stix-shifter update to v6 (6.0.3)

1.7.3 (2023-07-26)
==================

Added
-----

- stix-shifter data source interface diagnosis module
- ``stix-shifter-diag``: stix-shifter data source interface diagnosis utility
- Docs on ``stix-shifter-diag``
- Error message update to point to ``stix-shifter-diag``
- Unit tests of the diagnosis module and CLI utility

1.7.2 (2023-07-26)
==================

Added
-----

- Minimal version requirements for all dependencies
- param ``cool_down_after_transmission`` in stix-shifter interface
- Unit tests on empty input variable for commands
- ``lark-js`` support for ``kestrel.lark`` #371

Changed
-------

- Keep stix-shifter to v5 (not v6) to avoid a dependency specification issue

Fixed
-----

- Fast translation bug on ``group`` keyword in stix-shifter mapping #370
- ``typeguard`` old version cause exception
- Exception with empty variable #254

1.7.1 (2023-07-13)
==================

Added
-----

- LIMIT keyword in GET/FIND
- LIMIT support in stix-shifter interface and stix-bundle interface
- Unit tests for LIMIT
- Documentation for LIMIT
- New transform function RECORD
- Documentation for RECORD
- Unit tests for RECORD

Changed
-------

- Use prefetch results for GET/FIND if prefetched; instead of merging results with local/main query

Fixed
-----

- stix-shifter interface translator error msg passing bugs
- stix-shifter interface transmitter error msg passing bug
- Infinite loop in stix-shifter interface transmitter
- stix-shifter connector pip uninstall hanging issue
- Prefetch logic error with empty return
- Dataframe index error in CSV export

1.7.0 (2023-06-14)
==================

Added
-----

- Multi-process support for stix-shifter data source interface

    - Each native data source query is executed in a subprocess
    - A pool of translators are created to pick up translation tasks for each transmitted page/batch
    - Ingestion is serialized in main proccess to avoid multi-process execution for SQLite
    - Two queues between transmitter/translator and translator/ingestor are used
    - Both stix-shifter translation and firepit fast-translation are supported
    - With debug flag, the translated results (JSON or DataFrame) will be dump to disk
    - Unit tests for the translator subprocess in different modes

- Additional syntax/keywords on singular timeunits

- New variable transformer function ``ADDOBSID``

    - Add new syntax and codegen
    - Add additional documentatoin

- Unit tests on CLI

    - Invoking with ``kestrel x.hf``
    - Invoking with ``python -m kestrel x.hf``

Fixed
-----

- No dumped data in stix-shifter interface when debug is enabled
- Multiprocessing conflict with ``runpy``
- STIX-shifter module verification failure due to pypi website update

Removed
-------

- Deprecated functions in ``kestrel/codegen/relations.py``

Changed
-------

- Examples in Kestrel config YAML

1.6.1 (2023-05-31)
==================

Changed
-------

- Kestrel variable definition syntax changed back to ``CNAME`` from ``ECNAME``
- stix-shifter data source profile config changes

    - Replace ``result_limit`` with ``retrieval_batch_size``
    - Replace ``timeout`` with ``single_batch_timeout``
    - Add default values for the configs
    - Document updates
    - The new fields will be processed by Kestrel before given to stix-shifter

- Replace stix-shifter sync APIs with async APIs

Added
-----

- Scalability end-to-end testing for large query with multiple pages
- Test cases for new stix-shfiter data source configs

Fixed
-----

- Temporary fix of stix-shifter/issues/1493

    - Add retry-once logic if server timeout (busy CPU on the client side)
    - Nullify the pipelining; need better long-term fix to enable it

- Fixed bugs and reimplement ``transmission_complete()`` in stix-shifter data source interface

1.6.0 (2023-05-17)
==================

Changed
-------

- Upgrade stix-shifter from v4 to v5 in the stix-shifter datasource interface
- Bump stix-shifter version to v5.3.0 to include latest Elastcisearch ECS mappings
- Restrict scopes of Github workflows to eliminate unnecessary executions

Added
-----

- stix-shifter datasource interface query procedure pipelining: a producer-consumer model for transmission and translation/ingestion
- Integration testing with stix-shifter and the first live data source---Elasticsearch
- Raw String implemented in Kestrel
- Documentation on raw String

Fixed
-----

- Logging module reimplemented to fix #334
- asyncio bug in ``tests/test_fast_translate.py``

1.5.14 (2023-04-19)
===================

Fixed
-----

- A bug in firepit v2.3.16 when fast translation is in use; fixed in firepit v2.3.17
- Improved logic on prefetch skipping; fix #322
- Fixing several unit tests with the improved prefetch skipping logic

1.5.13 (2023-04-19)
===================

Added
-----

- Using process UUID for process identification #252 #93
- Connector timeout config in stix-shifter data source interface doc

Fixed
-----

- Library deprecation: pkg_resources
- Invalid STIX bundle (missing identity SCO type) yielded by stix-shifter data source interface

Removed
-------

- Python 3.7 support

1.5.12 (2023-03-21)
===================

Fixed
-----

- Typo in pip install suggestion for stix-shifter modules
- Updated github workflows
- Vars created via assign should not lose reference attributes #312

1.5.11 (2023-03-15)
===================

Added
-----

- Alpine Linux install requirement
- Actionable suggestion in stix-shifter connector error msg
- Relation between config files in documentation

Fixed
-----

- stix-shifter 4.6.2 fixing elastic_ecs connector get_pagesize error
- firepit 2.3.14 improving fast translation

1.5.10 (2023-03-07)
===================

Added
-----

- Fast translation as an option for stix-shifter datasource interface
- Configurable ``RETRIEVAL_BATCH_SIZE`` in stix-shifter interface
- Doc on configurable ``RETRIEVAL_BATCH_SIZE``
- Tests on stix-shifter interface functions

Fixed
-----

- Fast translation integration bug with asyncio

Changed
-------

- Default ``RETRIEVAL_BATCH_SIZE`` in stix-shifter interface set to 2000
- stix-shifter API argument name change to be consistent across connectors
- stix-shifter minimal version for elastic_ecs connector pagination support
- stix-shifter minimal version for elastic_ecs connector mapping update

1.5.9 (2023-02-17)
==================

Fixed
-----

- stix-shifter elastic_ecs connector (without pagination support yet) incompatibility

1.5.8 (2023-02-16)
==================

Added
-----

- Uninstall the incorrect version of stix-shifter connector if exist #288
- Reference in attribute support for expression #290
- Overview page for installation/setup doc

Changed
-------

- Default ``RETRIEVAL_BATCH_SIZE`` in stix-shifter interface increased from 512 to 10000
- Retrieval (tranmission) stopping criteria upgrade to support multi-page query in the next stix-shifter release (targeting v4.6.1)
- Runtime installation doc structure/layout upgrade

1.5.7 (2023-02-02)
==================

Added
-----

- New escaping (regex) test case for parser
- New escaping (regex) test case via stix-bundle interface

Fixed
-----

- Readthedocs bullet rendering error #278

Changed
-------

- Fixture teardown improvement in tests
- Stix-shifter version specification relax
- Up-to-date black styling (standard changes)

1.5.6 (2023-01-26)
==================

Added
-----

- Dialect configuration to stix-shifter interface doc #270
- Dozens of unit tests for the auto-complete function

Fixed
-----

- Stix-shifter 4.6.0 stix-bundle connector time range requirement
- Reimplement the Kestrel auto-complete function to fix broken logic #264

1.5.5 (2023-01-21)
==================

Added
-----

- Kestrel doc for v1.5 syntax, mostly the language specification chapter

    - New section on the Kestrel patterning: Extended Centered Graph Pattern (ECGP)
    - New section on entity, attribute, and related mechanisms
    - Commands section updated with v1.5 syntax
    - Interface section rewritten with much more details
    - Concepts/terminology section updated

Changed
-------

- ``ASSIGN`` and ``MERGE`` commands now require a return variable

1.5.4 (2023-01-11)
==================

Added
-----

- Faster dependency installation for all github workflows using Python wheels
- Python 3.11 in unit test (github workflow)

Fixed
-----

- STIX-shifter module verification failure due to pypi website update
- codecov rate limit for public repo

1.5.3 (2022-11-23)
==================

Added
-----

- Multiple test cases for escaped string parsed with main/ECGP parsers

Fixed
-----

- Escaped string in value for both ECGP and argument
- Token prefix not handled in 

Changed
-------

- Use firepit time function for timestamp parsing
- Update Lark rule ``transform`` to ``vtrans`` to avoid Lark special function misfire

Removed
-------

- Explicit dependency ``python-dateutil``

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
