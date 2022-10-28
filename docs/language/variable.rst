================
Kestrel Variable
================

A Kestrel variable is a list of homogeneous entities---all entities in a
variable share the same type, for example, ``process``, ``network-traffic``, ``file``.
Each type of entities has its specialized attributes, for example, ``process`` has
``pid``, ``network-traffic`` has ``dst_port``, ``file`` has ``hashes``.  You can
use the ``INFO`` Kestrel command to see any variable's type and attributes.

When using the STIX-Shifter_ data source interface, Kestrel loads `STIX Cyber
Observable Objects`_ (SCO) as basic telemetry data. The entity types and their
attributes are defined in `STIX specification`_. Note that STIX_ is open to
both custom attributes and custom entity types, and the entity type and
available attributes actually depends on the exact data source.

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
.. _STIX-Shifter: https://github.com/opencybersecurityalliance/stix-shifter
.. _STIX specification: https://docs.oasis-open.org/cti/stix/v2.1/stix-v2.1.html
.. _STIX Cyber Observable Objects: http://docs.oasis-open.org/cti/stix/v2.0/stix-v2.0-part4-cyber-observable-objects.html
