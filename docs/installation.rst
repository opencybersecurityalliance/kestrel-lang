============
Installation
============

Install the Kestrel runtime, Kestrel Jupyter front-end, and STIX-shifter connector modules.

Operating Systems
=================

Currently, Kestrel is supported on Linux and macOS.

Requirements
============

Python
------

This project builds on Python 3. Refer to the `Python installation guide`_ if you do not have Python 3.

SQLite
------

If you are using following Linux distributions or newer, the SQLite requirement is
already met:

- Archlinux
- Debian 10
- Fedora 33
- Gentoo
- openSUSE Leap 15.2
- RedHat 8
- Ubuntu 20.04 LTS

Otherwise, check the SQLite version in a terminal and upgrade ``sqlite3 >=
3.24`` as needed, which is required by `firepit`_, a Kestrel dependency, in its
default configuration:

.. code-block:: console

    $ sqlite3 --version

Runtime Installation
====================

You can install Kestrel runtime from `stable release`_ or `nightly built
version (source code)`_. Either way installs all packages in the
``kestrel-lang`` repository, and dependent packages, such as ``firepit`` and
``stix-shifter``.

It is a good practice to install Kestrel in a `Python virtual environment`_ so
all dependencies will be the latest. You can easily setup, activate, and
update a Python virtual environment named *huntingspace*:

.. code-block:: console

    $ python -m venv huntingspace
    $ . huntingspace/bin/activate
    $ pip install --upgrade pip setuptools wheel

Stable Release
--------------

Run this command in your terminal (*huntingspace* activated):

.. code-block:: console

    $ pip install kestrel-lang

Nightly Built Version (Source Code)
-----------------------------------

Run this command in your terminal (*huntingspace* activated):

.. code-block:: console

    $ git clone git://github.com/opencybersecurityalliance/kestrel-lang
    $ cd kestrel-lang && pip install .

Front-Ends Installation
=======================

Kestrel runtime currently supports three front-ends
(:ref:`kestrel_in_a_nutshell`):

1. Command-line execution utility ``kestrel``: Installed with the
   package ``kestrel``. 

.. code-block:: console

    $ kestrel [-h] [-v] [--debug] hunt101.hf

2. Kestrel Jupyter Notebook kernel: Must install and set up the
   `kestrel-jupyter`_ package (`Jupyter Notebook`_ dependencies will be
   automatically installed if they do not exist):

.. code-block:: console

    $ pip install kestrel-jupyter
    $ python -m kestrel_jupyter_kernel.setup

3. Python API:

- Start a Kestrel session in Python directly. See more at :doc:`source/kestrel.session`.

- Use `magic command`_ in iPython environment. Check `kestrel-jupyter`_ package for usage.

STIX-shifter Connector Installation
===================================

Among :ref:`data-source-and-analytics-interfaces`, STIX-shifter is the main
data source interface currently implemented by the Kestrel runtime.
`STIX-shifter`_ provides a federated search interface against more than a dozen
EDRs, NDRs, and SIEM systems for data retrieval.

Because of the federated nature of STIX-shifter, the project releases a string
of Python packages (called *connectors* of STIX-shifter) for each data source.
Depending on the data source you are connecting to, e.g., Sysmon data stored in
Elasticsearch, you need to install the corresponding connector such as
`stix-shifter-modules-elastic-ecs`:

.. code-block:: console

    $ pip install stix-shifter-modules-elastic-ecs

STIX-shifter Data Source Config
===============================

After installing the STIX-shifter connector, you need to tell a Kestrel
front-end, e.g., Jupyter, details of the data source you are connecting to.
This is done by exporting three environment variables for each data source, e.g.:

.. code-block:: console

    $ export STIXSHIFTER_HOST101_CONNECTOR=elastic_ecs
    $ export STIXSHIFTER_HOST101_CONNECTION='{"host":"elastic.securitylog.company.com", "port":9200, "indices":"host101"}'
    $ export STIXSHIFTER_HOST101_CONFIG='{"auth":{"id":"VuaCfGcBCdbkQm-e5aOx", "api_key":"ui2lp2axTNmsyakw9tvNnw"}}'

(Optional) Kestrel Analytics
============================

Want to have some Kestrel analytics ready at your fingertip? Threat
intelligence enrichments like SANS API? Domain name lookup for IP addresses?
Finding IP geolocations and pin them on an interactive map? Invoking machine
learning inference function? Clone the community-contributed Kestrel analytics
repo to start:

.. code-block:: console

    $ git clone https://github.com/opencybersecurityalliance/kestrel-analytics.git

Go to the `analytics` directory and build the analytics docker containers to
``APPLY`` in your hunt.

Kestrel in Action
=================

Now the Kestrel runtime is set up and you can run a Kestrel huntflow with the
command-line utility or launch a Jupyter service for developing a huntbook
interactively (*huntingspace* activated):

.. code-block:: console

   $ jupyter notebook

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/
.. _Python virtual environment: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/
.. _Github repo: https://github.com/opencybersecurityalliance/kestrel-lang
.. _kestrel-jupyter: http://github.com/opencybersecurityalliance/kestrel-jupyter
.. _Jupyter Notebook: https://jupyter.org/
.. _magic command: https://ipython.readthedocs.io/en/stable/interactive/magics.html
.. _firepit: https://github.com/opencybersecurityalliance/firepit
.. _STIX-shifter: https://github.com/opencybersecurityalliance/stix-shifter
