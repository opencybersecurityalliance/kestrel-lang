===================
Entity and Variable
===================

We discuss the data model from language perspective (how end users are
performing entity-based reasoning), especially common entities and Kestrel
variable.

Entities in Kestrel
===================

:ref:`language/tac:Entity` defines each object in :ref:`language/tac:Record`.
In theory, Kestrel can handle any type of entities as data sources provide. In
real-world uses, users may primarily use
:doc:`../source/kestrel_datasource_stixshifter.interface` (the first supported
data source interface) to retrieve data. `stix-shifter`_ is a federated search
engine with `stix-shifter connectors`_ to a variety of data sources). And the
retrieved data naturally reside in `STIX`_, so the entities retrieved through
:doc:`../source/kestrel_datasource_stixshifter.interface` are `STIX Cyber
Observable Objects`_ (SCO), which defines the types of entities and the
attributes for each entity type.

Note that STIX_ is open to both custom attributes and custom entity types, and
each `stix-shifter connectors`_ could implement entities and attributes beyond
standard STIX SCO. For example, many `stix-shifter connectors`_ yield entities
defined in `OCA/stix-extension`_ like ``x-oca-asset``, which is an entity of a
host/VM/container/pod.

Common Entities and Attributes
------------------------------

Below is a list of common entities and attributes when using
:doc:`../source/kestrel_datasource_stixshifter.interface`:

.. list-table::

  * - **Entity Type**
    - **Attribute Name**
    - **Value Example**
  * - process
    - | name
      | pid
      | command_line
      | parent_ref.name
      | binary_ref.name
      | x_unique_id
    - | powershell.exe
      | 1234
      | powershell.exe -Command $Res = 0;
      | cmd.exe
      | powershell.exe
      | 123e4567-e89b-12d3-a456-426614174000
  * - network-traffic
    - | src_ref.value
      | src_port
      | dst_ref.value
      | dst_port
      | protocols
      | src_byte_count
      | dst_byte_count
    - | 192.168.1.100
      | 12345
      | 192.168.1.1
      | 80
      | http, tcp, ipv4
      | 96630
      | 56600708
  * - file
    - | name
      | size
      | hashes.SHA-256
      | hashes.SHA-1
      | hashes.MD5
      | parent_directory_ref.path
    - | cmd.exe
      | 25536
      | fe90a7e910cb3a4739bed918...
      | a9993e364706816aba3e2571...
      | 912ec803b2ce49e4a541068d...
      | C:\\Windows\\System32
  * - directory
    - | path
    - | C:\\Windows\\System32
  * - ipv4-addr
    - value 
    - 192.168.1.1
  * - ipv6-addr
    - value
    - 2001:0db8:85a3:0000:0000:8a2e:0370:7334
  * - mac-addr
    - value
    - 00:00:5e:00:53:af
  * - domain-name
    - value
    - example.com
  * - url
    - value
    - https://example.com/research/index.html
  * - user-account
    - | user_id
      | account_login
    - | 1001
      | ubuntu
  * - email-addr
    - | value
      | display_name
    - | john@example.com
      | John Doe
  * - windows-registry-key
    - key
    - HKEY_LOCAL_MACHINE\\System\\Foo\\Bar
  * - autonomous-system
    - | number
      | name
    - | 15139
      | Slime Industries
  * - software
    - | name
      | version
      | vendor
    - | Word
      | 2002
      | Microsoft
  * - x509-certificate
    - | issuer
      | hashes.SHA-256
      | hashes.SHA-1
      | hashes.MD5
    - | C=ZA, ST=Western Cape, L=Cape Town ...
      | fe90a7e910cb3a4739bed918...
      | a9993e364706816aba3e2571...
      | 912ec803b2ce49e4a541068d...
  * - x-oca-asset
    - | name
      | os_name
      | os_version
    - | server101
      | RedHat
      | 8


Kestrel Variable
================

A Kestrel variable is a list of homogeneous entities---all entities in a
variable share the same type, for example, ``process``, ``network-traffic``, ``file``.

Naming
------

The naming rule of a Kestrel variable follows the variable naming rule in C
language: a variable starts with an alphabet or underscore ``_``, followed by
any combination of alphabet, digit, and underscore. There is no length limit
and a variable name is case sensitive.

Mutability
----------

Unlike immutable variables in pure functional programming languages, variables
in Kestrel are mutable. They can be partially updated, e.g., new attributes
added through an analytics, and they can be overwritten by a variable
assignment to an existing variable.

Data Representation
-------------------

A Kestrel variable points to a *data table*, which stores entity information
regarding their appearances in different records.  Each column is an attribute
of the entity. Each row contains information of an :ref:`language/tac:Entity`
extracted from a single :ref:`language/tac:Record`.  Since the same entity
could appear in multiple records, multiple rows could belong to the same
entity.

For example, there are 5 records/events in an Elasticserach index that contain
different pieces of information about a process (pid ``1234``):

- One record is about creation/fork/spawn of the process.
- One record is about a file access operation of the process.
- Three records are about network communication of the process.

When a user get the process into a Kestrel variable ``proc``:

.. code-block:: elixir

    proc = GET process FROM stixshifter://sample_elastic_index WHERE pid = 1234

The result variable ``proc`` contains 1 entity (process ``1234``) while there
are 5 rows in the data table of the variable, each of which stores the process
related information extracted from one of the 5 records/events in
Elasticsearch.

Similarly, a variable could have 3 entities, each of which is seen in 6
records/events. In total, the data table of the variable has 18 rows, and the
columns (set of attributes of the entities in the variable) is the union of all
attributes seen in all rows. One can use the :ref:`language/commands:INFO`
command to show information of the variable (how many entities; how many
records; what are the attributes) and the :ref:`language/commands:DISP` command
to show the data table of the variable.

Internally, Kestrel stores the data table of each variable in a relational
database (implemented in `firepit`_ as a view of an entity table).  When
Kestrel passes a variable to an analytics via the
:doc:`../source/kestrel_analytics_python.interface`, the data table in the
variable is formated as a `Pandas Dataframe`_. When Kestrel passes a variable
to an analytics via the :doc:`../source/kestrel_analytics_docker.interface`,
the data table in the variable is dumped into a parquet file before given to
the analytics. In addition, Kestrel has :ref:`language/commands:SAVE` and
:ref:`language/commands:LOAD` commands to dump the data table of a variable
to/from a CSV or parquet file.


Variable Transforms
-------------------

When Kestrel extracts :ref:`language/tac:Entity` from
:ref:`language/tac:Record` to construct the data table for a variable,
only information about each entity is extracted, such as attributes that
describe the entity. However, a record/event may have some additional
information besides all entities in the record/event, such as when the record
is observed or when the event happened.

Such information is not in a variable by default, but they could be useful in a
hunt. In Kestrel, there are *variable transforms* that transforms the data
table of a variable into other formats such as a data table with additional
columns of record/event/(STIX observation) timestamps.

One can use the ``TIMESTAMPED`` keyword as a function fulfill the
transformation (resulting in a new column ``first_observed`` to all rows in the
variable data table):

.. code-block:: elixir

   ts_procs = TIMESTAMPED(procs)

Hunters can then apply time-series analysis analytics or visualization
analytics using the new column ``first_observed``. Check for an example in the
huntbook ``5.  Apply a Kestrel Analytics.ipynb`` in the online `Kestrel
Tutorial`_.

Advanced Topics
===============

Entity Data Prefetch
--------------------

Entity Identification
---------------------


.. _STIX: https://oasis-open.github.io/cti-documentation/stix/intro.html
.. _stix-shifter: https://github.com/opencybersecurityalliance/stix-shifter
.. _stix-shifter connectors: https://github.com/opencybersecurityalliance/stix-shifter/blob/develop/OVERVIEW.md#available-connectors
.. _STIX Cyber Observable Objects: http://docs.oasis-open.org/cti/stix/v2.0/stix-v2.0-part4-cyber-observable-objects.html
.. _OCA/stix-extension: https://github.com/opencybersecurityalliance/stix-extensions
.. _Pandas Dataframe: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html
.. _firepit: https://github.com/opencybersecurityalliance/firepit
.. _Kestrel Tutorial: https://mybinder.org/v2/gh/opencybersecurityalliance/kestrel-huntbook/HEAD?filepath=tutorial
