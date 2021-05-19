===============================
Kestrel Threat Hunting Language
===============================

.. image:: https://img.shields.io/pypi/pyversions/kestrel-lang
        :target: https://pypi.python.org/pypi/kestrel-lang/

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
        :target: https://github.com/psf/black

.. image:: https://img.shields.io/pypi/v/kestrel-lang
        :target: https://pypi.python.org/pypi/kestrel-lang/

.. image:: https://img.shields.io/pypi/dm/kestrel-lang
        :target: https://pypi.python.org/pypi/kestrel-lang/

.. image:: https://readthedocs.org/projects/kestrel/badge/?version=latest
        :target: https://kestrel.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

What is Kestrel? How to install? How to connect to data sources? How to write your first hunt flow?

You can find all the answers at `Kestrel documentation hub`_. A quick primer is below.

.. _Kestrel documentation hub: https://kestrel.readthedocs.io/

===================
Introducing Kestrel
===================

We introduce Kestrel as a layer of abstraction to stop repeating ourselves in
cyber threat hunting.

- Kestrel language: a threat hunting language for a human to express *what to
  hunt*.

    - expressing the knowledge of *what* in patterns, analytics, and hunt flows.
    - composing reusable hunting flows from individual hunting steps.
    - reasoning with human-friendly entity-based data representation abstraction.
    - thinking across heterogeneous data and threat intelligence sources.
    - applying existing public and proprietary detection logic as analytics.
    - reusing and sharing individual hunting steps and entire hunt books.

- Kestrel runtime: a machine interpreter that deals with *how to hunt*.

    - compiling the *what* against specific hunting platform instructions.
    - executing the compiled code locally and remotely.
    - assembling raw logs and records into entities for entity-based reasoning.
    - caching intermediate data and related records for fast response.
    - prefetching related logs and records for link construction between entities.
    - defining extensible interfaces for data sources and analytics execution.

============
Architecture
============

The entire Kestrel runtime consists following Python packages:

- ``kestrel`` (in *kestrel-lang* repository): the interpreter including
  parser, session management, code generation, data source and
  analytics interface managers, and a command line front end.

- ``firepit`` (in *firepit* repository): the Kestrel internal data storage
  ingesting data from data sources, caching related data, and linking records
  against each Kestrel variable, 

- ``kestrel_datasource_stixshifter`` (in *kestrel-lang* repository): the
  STIX-Shifter data source interface for managing data sources via
  STIX-Shifter.

- ``kestrel_datasource_stixbundle`` (in *kestrel-lang* repository): the data
  source interface for ingesting static telemetry data that is already sealed
  in STIX bundles.

- ``kestrel_analytics_docker`` (in *kestrel-lang* repository): the analytics
  interface that executes analytics in docker containers.

- ``kestrel_jupyter_kernel`` (in *kestrel-jupyter* repository): the Kestrel
  Jupyter Notebook kernel to use Kestrel in a Jupyter notebook.

- ``kestrel_ipython`` (in *kestrel-jupyter* repository): the iPython *magic
  command* realization for writing native Kestrel in iPython.
  
============
Installation
============

Install the Kestrel runtime plus additional front ends such as Kestrel Jupyter
Notebook kernel.


Requirements
============

This project builds on Python 3. Refer to the `Python installation guide`_ if you do not have Python 3.

The preferred way to install Kestrel is via `pip`_. Please upgrade `pip`_ to the latest version before install:

.. code-block:: console

    $ pip install --upgrade pip

Runtime Installation
====================

One can install Kestrel runtime from `stable release`_ or `source code`_.
Either way installs all packages in the ``kestrel-lang`` repository, and
dependent packages such as ``firepit`` and ``stix-shifter``. Check the
architecture section in :doc:`overview` to understand more.

You can install as a normal user, root, or in a `Python virtual environment`_.

Stable Release
--------------

Run this command in your terminal:

.. code-block:: console

    $ pip install kestrel-lang

Source Code
-----------

1. install and upgrade Python building packages ``setuptools`` and ``wheel``:

.. code-block:: console

    $ pip install --upgrade pip setuptools wheel

2. clone the source from the `Github repo`_:

.. code-block:: console

    $ git clone git://github.com/IBM/kestrel-lang
    $ cd kestrel-lang

3. (optional) switch to the `develop` branch if you want the nightly built version:

.. code-block:: console

    $ git checkout develop

4. install all packages from the repo:

.. code-block:: console

    $ pip install .

Runtime Front Ends
==================

Kestrel runtime currently supports three front ends (see architecture figure in :doc:`overview`):

1. Command line execution utility ``kestrel``: this is installed with the
   package ``kestrel``. 

.. code-block:: console

    $ kestrel [-h] [-v] [--debug] hunt101.hf

2. Kestrel Jupyter Notebook kernel: need to install and setup the
   `kestrel-jupyter`_ package (`Jupyter Notebook`_ dependencies will be
   automatically installed if not exist):

.. code-block:: console

    $ pip install kestrel-jupyter
    $ python -m thl_jupyter_kernel.setup

3. Python API:

    - Start a Kestrel session in Python directly. See more at :doc:`source/kestrel.session`.

    - Use `magic command`_ in iPython environment. ``kestrel-jupyter`` required.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/
.. _Python virtual environment: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/
.. _Github repo: https://github.com/IBM/kestrel-lang
.. _kestrel-jupyter: http://github.com/IBM/kestrel-jupyter
.. _Jupyter Notebook: https://jupyter.org/
.. _magic command: https://ipython.readthedocs.io/en/stable/interactive/magics.html
