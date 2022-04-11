Connect to Data Sources
-----------------------

Data sources, e.g., an EDR, a SIEM, a firewall, provide raw or processed data
for hunting. Kestrel hunt steps such as :ref:`language:GET` and
:ref:`language:FIND` generate code or queries to retrieve data, e.g., system
logs or alerts, from data sources.

Kestrel Data Source Abstraction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Kestrel manages data sources in a two-level abstraction: a data source
registers at a :doc:`../source/kestrel.datasource.interface`, which defines the
way how a set of data sources are queried and ingested into Kestrel. In other
words, Kestrel manages multiple data source interfaces at runtime, each of
which manages a set of data sources with the same query method and ingestion
procedure.  Learn more about the abstraction in :ref:`language:Data Source And
Analytics Interfaces`.

Kestrel by default ships with the two most common data source interfaces:

- :doc:`../source/kestrel_datasource_stixshifter.interface`

    - leverage `STIX-shifter`_ as a federated search layer
    - talk to more then a dozen of different data sources

- :doc:`../source/kestrel_datasource_stixbundle.interface`

    - use canned STIX bundle data for demo or development

Setup STIX-shifter Data Source
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you get credentials of a data source, you need to tell Kestrel how to use
them to connect. In other words, you need to create a profile for each data
source. The profile:

- names the data source to refer to in a huntbook,
- specifies which `STIX-shifter connector`_ to use,
- specifies how to connect to the data source,
- gives additional configuration if needed for data source access.

Check :doc:`../source/kestrel_datasource_stixshifter.interface` for details and
examples of adding data source profiles.

.. _STIX-shifter connector: https://github.com/opencybersecurityalliance/stix-shifter/blob/develop/OVERVIEW.md#available-connectors
.. _STIX-shifter: https://github.com/opencybersecurityalliance/stix-shifter
