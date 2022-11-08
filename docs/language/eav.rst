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
Each type of entities has its specialized attributes, for example, ``process`` has
``pid``, ``network-traffic`` has ``dst_port``, ``file`` has ``hashes``.  You can
use the ``INFO`` Kestrel command to see any variable's type and attributes.

The naming rule of a Kestrel variable follows the variable naming rule in C
language: a variable starts with an alphabet or underscore ``_``, followed by
any combination of alphabet, digit, and underscore. There is no length limit
and a variable name is case sensitive.

Unlike immutable variables in pure functional programming languages, variables
in Kestrel are mutable. They can be partially updated, e.g., new attributes
added through an analytics, and they can be overwritten by a variable
assignment to an existing variable.


Variable Transforms
===================

TIMESTAMPED
-----------

STIX data from STIX-Shifter_ comes in the form of "observations," or the
``observed-data`` STIX Domain Object (SDO).  This object contains (or
references) SCOs, along with a time range for when those observables were
actually seen.

SCOs themselves do not contain any information for when they were observed,
but you can retrieve SCOs with timestamps from those observations by using the
``TIMESTAMPED`` transform:

::

   ts_scos = TIMESTAMPED(scos)

The result of this transform is no longer a list of entities, but a data
table containing the timestamp of each observation of the entities.


.. _STIX: https://oasis-open.github.io/cti-documentation/stix/intro.html
.. _stix-shifter: https://github.com/opencybersecurityalliance/stix-shifter
.. _stix-shifter connectors: https://github.com/opencybersecurityalliance/stix-shifter/blob/develop/OVERVIEW.md#available-connectors
.. _STIX Cyber Observable Objects: http://docs.oasis-open.org/cti/stix/v2.0/stix-v2.0-part4-cyber-observable-objects.html
.. _OCA/stix-extension: https://github.com/opencybersecurityalliance/stix-extensions
