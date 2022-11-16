===================
Entity and Variable
===================

We discuss the data model from language perspective (how end users are
performing entity-based reasoning), to implementation logic.

Entities in Kestrel
===================

:ref:`language/tac:Entity` defines an object in a :ref:`language/tac:Record`.
In theory, Kestrel can handle any type of entities as data sources provide. In
real-world uses, users could primarily use
:doc:`../source/kestrel_datasource_stixshifter.interface`---the first Kestrel
supported data source interface---to retrieve data. `stix-shifter`_ is a
federated search engine with `stix-shifter connectors`_ to a variety of data
sources. The retrieved data through
:doc:`../source/kestrel_datasource_stixshifter.interface` is STIX `Observed
Data`_, and the entities in it are `STIX Cyber Observable Objects`_ (SCO), the
types and attributes of which are formally defines in STIX.

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
      | account_type
      | is_privileged
    - | 1001
      | ubuntu
      | unix
      | true
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

Kestrel variables are mutable. They can be partially updated, e.g., new
attributes added through an analytics, and they can be overwritten by a
variable assignment to an existing variable.

Data Representation
-------------------

A Kestrel variable points to a *data table*, which stores entity information
regarding their appearances in different records. Each column is an attribute
of the entities. Each row contains information of an :ref:`language/tac:Entity`
extracted from a single :ref:`language/tac:Record`. Since the same entity could
appear in multiple records, multiple rows could contain information of the same
entity (extracted from different records).

Using the 5-Elasticsearch-record example in :ref:`language/tac:Entity`, assume
the 5 records are all around process with pid ``1234``, a user can get them all
into a Kestrel variable ``proc``:

.. code-block:: coffeescript

    proc = GET process FROM stixshifter://sample_elastic_index WHERE pid = 1234

The result variable ``proc`` contains 1 entity (process ``1234``) while there
are 5 rows in the data table of the variable, each of which stores the process
related information extracted from one of the 5 records in Elasticsearch.

Similarly, a variable could have 3 entities, each of which is seen in 6
records. In total, the data table of the variable has 18 rows, and the
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
the container. In addition, Kestrel has :ref:`language/commands:SAVE` and
:ref:`language/commands:LOAD` commands to dump the data table of a variable
to/from a CSV or parquet file.


Variable Transforms
-------------------

When Kestrel extracts :ref:`language/tac:Entity` from
:ref:`language/tac:Record` to construct the data table for a variable, only
information about each entity is extracted, such as attributes of that entity.
However, a record may have some additional information besides all entities in
it, such as when the record is observed or when the event happened (if a record
is defined as an individual event by a data source).

Such information is not in a Kestrel variable, but they could be useful in a
hunt. In Kestrel, there are *variable transforms* that transforms the data
table of a variable into other formats such as a data table with additional
columns of record/event/(STIX `Observed Data`_) timestamps.

One can use the ``TIMESTAMPED`` keyword as a function to conduct such
transformation, which results in a new column ``first_observed`` in the
transformed data table:

.. code-block:: coffeescript

   ts_procs = TIMESTAMPED(procs)

Hunters can then apply time-series analysis analytics or visualization
analytics using the new column ``first_observed``. Check for an example in the
3rd example of our tutorial huntbook `5. Apply a Kestrel Analytics.ipynb`_.

Advanced Topics
===============

Kestrel implements :ref:`language/tac:Entity-Based Reasoning`, while most
security data are not stored in this human-friendly view. More commonly, raw
data is generated/structured/stored in the view of :ref:`language/tac:Record`
around individual/aggregated system calls or network traffic.

Kestrel makes two efforts to lift the information in machine-friendly
:ref:`language/tac:Record` into human-friendly :ref:`language/tac:Entity` to
realize :ref:`language/tac:Entity-Based Reasoning`.

Entity Identification
---------------------

An :ref:`language/tac:Entity` could reside in multiple
:ref:`language/tac:Record`---Check an example in :ref:`language/tac:Entity`.
Kestrel recognizes the same entity across different records so it is possible
to construct the graph of entities and walk the graph to fulfill
:ref:`language/tac:Entity-Based Reasoning`.

Given the huntflow example in :ref:`language/tac:Entity-Based Reasoning`, some
records Kestrel get from the data source may contain information about the
creation of processes in ``pcs``, while another set of records may contain
information about network traffic of the process. Kestrel identifies the same
entity, e.g., process, across multiple records, to enable the execution of such
huntflow.

For many standard `STIX Cyber Observable Objects`_ entity types (detailed in
`Common Entities and Attributes`_), there could be one or a set of attributes
that uniquely identify the entity, e.g., the ``value`` attribute (IP address)
of ``ipv4-addr`` entities uniquely identify them; the ``key`` attribute
(registry key) of ``windows-registry-key`` entities uniquely identify them.
Kestrel uses these obvious identifiers if they exist.

However, the complexity comes regarding some important entities, especially
``process`` and ``file``. Some data sources (system monitors) generate a
universal identifier for a process, i.e., `UUID`_/GUID, while some others
don't. Even with UUID information avaliable, there is no standard STIX property
that is designed to hold this piece of information. In addition, the
description of an entity in a record may be incomplete due to the limited
monitoring capability, data aggregation, or software bug. For example, a record
may have ``pid`` and ``name`` information of a process, but another record may
only have ``pid`` but not ``name`` information of the same process.

Given the complexities, Kestrel implements a comprehensive mechanism for entity
identification, especially for ``process``:

    - It combines avaliable information of pid, ppid, name, and time observed
      to decide whether two process in two records are actually the same
      process (entity).

    - The observed time of a record does not infer how long the entity lives,
      while the same set of entity attributes could be reused by another
      entity, e.g., ``pid`` is recycled by OS. Kestrel inexactly infers the
      life span of an entity and identifies different entities with similar
      attributes. Parameters for customization are described in
      :doc:`../configuration`.

    - In the future, `UUID`_ will be used as the unique identifier of process
      when avaliable.

Entity Data Prefetch
--------------------

Since an :ref:`language/tac:Entity` could reside in multiple
:ref:`language/tac:Record` (example in :ref:`language/tac:Entity`), Kestrel
proactively asks data sources to get information about the entities in
different records when building Kestrel variables.

For example, the user may write the following pattern to get processes that
were executed from binary ``explorer.exe``:

.. code-block:: coffeescript

    procs = GET process FROM ... WHERE binary_ref.name = 'explorer.exe'

The data source may have records about network traffic of the target processes
but those records do not necessary have process binary information in them, so
those records will not be retrieved using the user specified pattern ``WHERE
binary_ref.name = 'explorer.exe'``. Thus, Kestrel needs to prefetch those
records to complete information about the entities such as:

    - Additional attributes of the entities not in the records retrieved by the
      user specified pattern.

    - Identifiers of connected entities to prepare execution of follow-up
      :ref:`language/commands:FIND` commands.

Kestrel implements a prefetch logic to generate additional queries to the data
source after a user specified pattern/query is executed (in the
:ref:`language/commands:GET` command). Prefetch is also used as the second step
to implement the :ref:`language/commands:FIND` command.

The high-level description of the :ref:`language/commands:FIND` command
realization:

    #. It obtains basic information about the connected entities from the local
       cache (in `firepit`_). The local cache contains prefetched records of
       the referred variable specified in ``FIND``. The previous prefetch
       retrieved records with connection information between entities in the
       two variables, as well as limited information of the new entities to be
       returned.

    #. It queries the data source to retrieve complete information around the
       new entities to return before putting all information into the return
       variable.

    #. For entity type ``process``, since there may be no unique identifier as
       discussed in `Entity Identification`_, Kestrel over-queries the data
       source with process ``pid`` in the above prefetch step, then it applies
       comprehensive logic to filter out records that do not belong to the
       returned processes. In the future, the logic could be embedded into data
       source queries, e.g., with process UUID support.

The prefetch feature can be turned off against a specific entity type or a
specific Kestrel command. This is useful if prefetch causes huge overhead with
some data sources. Edit Kestrel :doc:`../configuration` to customize the
prefetch behavior for a Kestrel deployment.


.. _STIX: https://oasis-open.github.io/cti-documentation/stix/intro.html
.. _stix-shifter: https://github.com/opencybersecurityalliance/stix-shifter
.. _stix-shifter connectors: https://github.com/opencybersecurityalliance/stix-shifter/blob/develop/OVERVIEW.md#available-connectors
.. _STIX Cyber Observable Objects: http://docs.oasis-open.org/cti/stix/v2.0/stix-v2.0-part4-cyber-observable-objects.html
.. _OCA/stix-extension: https://github.com/opencybersecurityalliance/stix-extensions
.. _Pandas Dataframe: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html
.. _firepit: https://github.com/opencybersecurityalliance/firepit
.. _5. Apply a Kestrel Analytics.ipynb: https://mybinder.org/v2/gh/opencybersecurityalliance/kestrel-huntbook/HEAD?filepath=tutorial/5.%20Apply%20a%20Kestrel%20Analytics.ipynb
.. _Observed Data: https://oasis-open.github.io/cti-documentation/stix/intro.html
.. _UUID: https://en.wikipedia.org/wiki/Universally_unique_identifier
