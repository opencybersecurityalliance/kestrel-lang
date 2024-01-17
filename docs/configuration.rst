=============
Configuration
=============

Kestrel loads user-defined configurations to override default values when the
runtimes start. Thus you can customize your Kestrel runtime by putting
configuration values in ``~/.config/kestrel/kestrel.yaml`` or any YAML file
with path specified in the environment variable ``KESTREL_CONFIG``.

Note: the Kestrel main config should not be confused with configurations for
data sources. In Kestrel, data sources are defined/grouped by each
:doc:`../source/kestrel.datasource.interface`. Each data source interface is a
Python package and has its own configuration file. For example,
:doc:`../source/kestrel_datasource_stixshifter.interface` describes the use and
configuration of STIX-shifter data sources.

Default Kestrel Configuration
=============================

.. literalinclude:: ../packages/kestrel_core/src/kestrel/config.yaml
   :language: yaml

Example of User-Defined Configurations
======================================

You can disable prefetch by creating ``~/.config/kestrel/kestrel.yaml`` with
the following:

.. code-block:: yaml

    prefetch:
      switch_per_command:
        get: false
        find: false

Kestrel will then not proactively search for logs/records for entities
extracted from the return of ``GET``/``FIND``, which will largely disable
followup ``FIND`` commands/steps.

Kestrel config supports expansion of environment variables, e.g., if a value in
the YAML file is ``$ENVX``, then the value is fetched from environment variable
``$ENVX`` Kestrel loads the config file.
