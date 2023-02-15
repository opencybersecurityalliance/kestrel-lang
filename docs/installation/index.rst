======================
Installation And Setup
======================

Kestrel utilizes computing resources and interacts with the world in three ways:

#. Huntflow organization and execution (core Kestrel compiler/interpreter/runtime)

#. Data retrieval (graph pattern matching, relation resolution, etc.)

#. Entity enrichment and extensible analytics (Kestrel analytics)

Accordingly, to install and setup Kestrel:

#. :doc:`Install the Kestrel runtime with a front-end of your choice<runtime>`
    Right after this step, you will be able to play with the
    :ref:`tutorial:Hello World Hunt`. However, this Kestrel environment does
    not have connections to any data sources or Kestrel analytics. 

#. :doc:`Configurate data sources to use<datasource>`
    Kestrel ships with two data source interfaces
    (:doc:`../source/kestrel_datasource_stixshifter.interface` and
    :doc:`../source/kestrel_datasource_stixbundle.interface`). However, Kestrel
    does not know what data sources you have.  You need to tell Kestrel where
    your data sources are and how to connect to them. This is done through data
    source configuration, especially :ref:`installation/datasource:Setup
    STIX-shifter Data Source`.

#. :doc:`Setup Kestrel analytics<analytics>`
    Kestrel ships with two analytics interfaces by default
    (:doc:`../source/kestrel_analytics_python.interface` and
    :doc:`../source/kestrel_analytics_docker.interface`). You need to :ref:`get
    analytics<installation/analytics:Kestrel Analytics Repo>` and register them
    under any of the interfaces, e.g., adding configuration to the
    :doc:`../source/kestrel_analytics_python.interface`.

.. toctree::
   :maxdepth: 2
   :hidden:

   runtime
   datasource
   analytics
