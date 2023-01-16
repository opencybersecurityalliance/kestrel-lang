==================
Kestrel Interfaces
==================

As a threat hunting language, Kestrel is designed to access a variety of data
sources and execute encapsulated analytics in every possible way, besides
assembling retrieval, transformational, enriching, and inspective :ref:`hunt
steps<language/tac:Hunt Step>` into :ref:`huntflows<language/tac:Hunt Flow>`.
In another word, Kestrel deals with different data sources in its retrieval
hunt steps as well as different analytics in its enriching hunt steps. It is
important to have an abstraction to be *adaptable* and *extensible* for data
sources and analytics---the design of Kestrel interfaces.

.. image:: ../images/interfaces.png
   :width: 100%
   :alt: Interface Illustration.

Illustrated in the figure above, Kestrel uses a two-level abstraction for both
data source and analytics: (i) a data source or analytics *interface* defines
how a data source or analytics executes, i.e., input, output, plus execution
mechanism, and (ii) each data source or analytics is developed to be executed
under one or more interfaces.

Each interface has one or multiple schema strings, for example,
``stixshifter://`` for the
:doc:`../source/kestrel_datasource_stixshifter.interface` and ``docker://`` for
the :doc:`../source/kestrel_analytics_docker.interface`. To use a specific data
source or analytics, a user specifies an identifier of the data source or
analytics as ``schema://name`` where ``name`` is the data source name or
analytics name.

Data Source Interfaces
======================

Kestrel currently implements two data source interfaces:
:doc:`../source/kestrel_datasource_stixshifter.interface` and
:doc:`../source/kestrel_datasource_stixbundle.interface`. The former employees
`STIX-shifter`_ as a federated search layer to reach to more than 30 different
data sources via `STIX-shifter connectors`_. The latter points to canned STIX
bundle data for demo or development purposes.

Find how to setup/use data sources in Kestrel at
:doc:`../installation/datasource`.

In real-world hunts, it is preferred to use a data source through
:doc:`../source/kestrel_datasource_stixshifter.interface` to avoid
re-implementing data pipelines that exist. As a hunter or hunting platform
developers, you may identify the `STIX-shifter connectors`_ to be used in your
orgainzation and customize them, e.g., update the translation mapping according
to your specific data schema. If no STIX-shifter connector exists for your data
source, you can follow the `STIX-shifter connector development guide`_ to
create one from a template by providing the API to the data source as well as
the mappings to/from STIX for translation.

You are not required to use `STIX-shifter`_ or the
:doc:`../source/kestrel_datasource_stixshifter.interface`. If you know how to
get data in STIX observations from your data sources, you can add new data
sources to :doc:`../source/kestrel_datasource_stixbundle.interface` to connect
to your data sources. If you don't like STIX and want direct connection to
Kestrel :ref:`language/eav:Data Representation`, you can create a new *data
source interface* to directly ingest data into `firepit`_, the Kestrel data
store. This can be achieved by creating a new Python class inheriting the
``AbstractDataSourceInterface`` class. More instructions are in
:doc:`../source/kestrel.datasource.interface` and `firepit documentation`_.

Analytics Interfaces
====================

Kestrel currently implements two analytics interfaces:
:doc:`../source/kestrel_analytics_python.interface` and
:doc:`../source/kestrel_analytics_docker.interface`. The former defines/runs a
Kestrel analytics as a Python function, while the latter defines/runs a Kestrel
analytics as a `Docker container`_.

Check out community-contributed Kestrel analytics at the `kestrel-analytics
repo`_ to get an idea of what analytics are possible to do in Kestrel. All
analytics in the repo can be invoked by either the Python or Docker analytics
interface. To use them via the
:doc:`../source/kestrel_analytics_python.interface`, one needs to tell the
interface where the analytic functions are by creating a
``pythonanalytics.yaml`` config file (sample provided at `kestrel-analytics
repo`_). To use them via the
:doc:`../source/kestrel_analytics_docker.interface`, one needs to do ``docker
build`` with the ``Dockerfile`` provided in each analytics folder. Visit
:doc:`../installation/analytics` to learn more about how to setup analytics.

Bring Your Own Analytics
------------------------

Of course these will not cover all analytics one needs in hunts. One can
quickly wrap a Python function into a Kestrel Python analytics as described in
:ref:`source/kestrel_analytics_python.interface:Develop a Python Analytics`.
One can also build a Kestrel analytics as a Docker container by following the
guide in :doc:`../source/kestrel_analytics_docker.interface` and the blog
`Building Your Own Kestrel Analytics`_. It is obvious that a Kestrel analytics
under the Docker interface can execute any code in any language, even binary
without source code, or an API to other services. In fact, a Kestrel analytics
under the Python interface can do the same by using the Python function as a
proxy to invoke complex analytic logic in any languages or binaries.

If both analytics interfaces are still not enough, for example, one already
have a collection of analytic functions as AWS Lambda functions, one can easily
develops a new Kestrel analytics interface to run them. Similar to developing a
new Kestrel data source interface, one needs to create a new Python class
inheriting the ``AbstractAnalyticsInterface`` class. More instructions are in
:doc:`../source/kestrel.analytics.interface`.

.. _STIX-shifter: https://github.com/opencybersecurityalliance/stix-shifter
.. _STIX-shifter connectors: https://github.com/opencybersecurityalliance/stix-shifter/blob/develop/OVERVIEW.md#available-connectors
.. _STIX-shifter connector development guide: https://github.com/opencybersecurityalliance/stix-shifter/tree/develop/adapter-guide
.. _firepit: https://github.com/opencybersecurityalliance/firepit
.. _firepit documentation: https://firepit.readthedocs.io/en/latest/?badge=latest
.. _Docker container: https://www.docker.com/resources/what-container/
.. _kestrel-analytics repo: https://github.com/opencybersecurityalliance/kestrel-analytics
.. _Building Your Own Kestrel Analytics: https://opencybersecurityalliance.org/posts/kestrel-custom-analytics/
