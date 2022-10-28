====================================
Data Source And Analytics Interfaces
====================================

Kestrel aims to keep it open and easy to add data source and analytics---not
only adding data source through the STIX-Shifter interface and adding analytics
through the docker interface, but even keeping the interfaces open and
extensible. You might start with a STIX-Shifter data source, and then want to
add another data source which already splits STIX observations---no
STIX-Shifter is needed. You can generate this capability to develop a data
source interface in parallel to STIX-Shifter and handle data from multiple
EDRs and SIEMs in your environment. Similar concepts apply to analytics.
You might start with writing Kestrel analytics in docker containers, but then
need to develop analytics around code that is executing in the cloud. What is
needed is the power to quickly add analytics interfaces besides the docker
one that is shipped with Kestrel.

To quickly develop new interfaces for data sources and
analytics, Kestrel abstracts the connection to data source and analytics with
two layers: Kestrel runtime communicates with interfaces and the interfaces
communicate with the data sources or analytics. Both data source and analytics
interfaces can be quickly developed by creating a new Python package following
the rules in :doc:`../source/kestrel.datasource.interface` and
:doc:`../source/kestrel.analytics.interface`.

.. image:: ../images/interfaces.png
   :width: 100%
   :alt: Interface Illustration.

Each interface has one or multiple schema strings, for example, ``stixshifter://`` for
the STIX-Shifter interface and ``docker://`` for the docker analytics
interface. To use a specific data source or analytics, a user specifies an
identifier of the data source or analytics as ``schema://name`` where ``name``
is the data source name or analytics name.
