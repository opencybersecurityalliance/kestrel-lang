============
Installation
============

Install the Kestrel runtime plus the Kestrel Jupyter front-end.

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
`kestrel-lang`_ repository, and dependent packages, such as `firepit`_ and
`STIX-shifter`_.

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

Kestrel in Action
=================

Now the Kestrel runtime is set up and you can run a Kestrel huntflow with the
command-line utility or launch a Jupyter service for developing a huntbook
interactively (*huntingspace* activated):

.. code-block:: console

   $ jupyter notebook

Optional: Kestrel Analytics
===========================

Want to have some Kestrel analytics ready at your fingertip? Threat
intelligence enrichments like SANS API? Domain name lookup for IP addresses?
Finding IP geolocations and pin them on an interactive map? Invoking machine
learning inference function? Clone the community-contributed Kestrel analytics
repo to start:

.. code-block:: console

    $ git clone https://github.com/opencybersecurityalliance/kestrel-analytics.git

Go to the `analytics` directory and build the analytics docker containers to
``APPLY`` in your hunt.

Optional: Debug Mode
====================

You can run Kestrel in debug mode by either use the ``--debug`` flag of the
Kestrel command-line utility, or create environment variable ``KESTREL_DEBUG``
with any value before launching Kestrel, which is useful when you use Kestrel
in Jupyter Notebook. In the debug mode, all runtime data including caches and
logs at debug level are at ``/tmp/kestrel/``.

.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/
.. _Python virtual environment: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/
.. _kestrel-lang: http://github.com/opencybersecurityalliance/kestrel-lang
.. _kestrel-jupyter: http://github.com/opencybersecurityalliance/kestrel-jupyter
.. _firepit: http://github.com/opencybersecurityalliance/firepit
.. _Jupyter Notebook: https://jupyter.org/
.. _magic command: https://ipython.readthedocs.io/en/stable/interactive/magics.html
.. _STIX-shifter: https://github.com/opencybersecurityalliance/stix-shifter
