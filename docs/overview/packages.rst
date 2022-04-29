The entire Kestrel runtime consists of the following Python packages:

- ``kestrel`` (repo: `kestrel-lang`_): The interpreter including parser,
  session management, code generation, data source and analytics interface
  managers, and a command-line front-end.

- ``firepit`` (repo: `firepit`_): The Kestrel internal data storage ingesting,
  processing, storing, caching, and linking data with Kestrel variables.

- ``kestrel_datasource_stixshifter`` (repo: `kestrel-lang`_): The STIX-Shifter
  data source interface for managing data sources via STIX-Shifter.

- ``kestrel_datasource_stixbundle`` (repo: `kestrel-lang`_): The data source
  interface for ingesting static telemetry data that is already sealed in STIX
  bundles.

- ``kestrel_analytics_python`` (repo: `kestrel-lang`_): The analytics interface
  that calls analytics in Python.

- ``kestrel_analytics_docker`` (repo: `kestrel-lang`_): The analytics interface
  that executes analytics in docker containers.

- ``kestrel_jupyter_kernel`` (repo: `kestrel-jupyter`_): The Kestrel Jupyter
  Notebook kernel to use Kestrel in a Jupyter notebook.

- ``kestrel_ipython`` (repo: `kestrel-jupyter`_): The iPython *magic command*
  realization for writing native Kestrel in iPython.

.. _kestrel-lang: http://github.com/opencybersecurityalliance/kestrel-lang
.. _firepit: http://github.com/opencybersecurityalliance/firepit
.. _kestrel-jupyter: http://github.com/opencybersecurityalliance/kestrel-jupyter
