===============
Install Runtime
===============

Install the Kestrel runtime and the Jupyter front-end.

Requirements
============

Operating Systems
-----------------

Supported OSes: Linux and macOS.

Python
------

Python 3 is required. Refer to the `Python installation guide`_ if you do not have Python 3.

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
`kestrel-lang`_ repository, and dependenies like `firepit`_ and
`STIX-shifter`_.

It is a good practice to install Kestrel in a `Python virtual environment`_ so
there will be no dependency conflict with Python packages in the system, plus
all dependencies will be the latest. You can easily setup, activate, and update
a Python virtual environment named ``huntingspace``:

.. code-block:: console

    $ python -m venv huntingspace
    $ . huntingspace/bin/activate
    $ pip install --upgrade pip setuptools

Stable Release
--------------

Run this command in your terminal (``huntingspace`` activated):

.. code-block:: console

    $ pip install kestrel-lang

Nightly Built Version (Source Code)
-----------------------------------

Run this command in your terminal (``huntingspace`` activated):

.. code-block:: console

    $ git clone git://github.com/opencybersecurityalliance/kestrel-lang
    $ cd kestrel-lang && pip install .

Front-Ends Installation
=======================

Kestrel runtime currently supports three front-ends
(:ref:`kestrel_in_a_nutshell`):

1. Command-line execution utility ``kestrel`` (installed in the
   package ``kestrel-lang``):

.. code-block:: console

    $ kestrel [-h] [-v] [--debug] hunt101.hf

2. Kestrel Jupyter Notebook kernel (if you plan to hunt in Jupyter with Kestrel):

.. code-block:: console

    $ pip install kestrel-jupyter
    $ python -m kestrel_jupyter_kernel.setup

3. Python API:

- Start a Kestrel session in Python directly. See more at :doc:`../source/kestrel.session`.

- Use `magic command`_ in iPython environment. Check `kestrel-jupyter`_ package for usage.

Start Your Hunt
===============

Now the Kestrel runtime is set up and you can run a Kestrel huntflow with the
command-line utility or launch a Jupyter service for developing a huntbook
interactively (``huntingspace`` activated):

.. code-block:: console

    $ jupyter notebook

What's to Do Next
=================

- :ref:`tutorial:Hello World Hunt`
- :doc:`datasource`
- :doc:`analytics`
- `Explore Kestrel huntbooks`_
- :doc:`../language`

.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/
.. _Python virtual environment: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/
.. _kestrel-lang: http://github.com/opencybersecurityalliance/kestrel-lang
.. _kestrel-jupyter: http://github.com/opencybersecurityalliance/kestrel-jupyter
.. _firepit: http://github.com/opencybersecurityalliance/firepit
.. _Jupyter Notebook: https://jupyter.org/
.. _magic command: https://ipython.readthedocs.io/en/stable/interactive/magics.html
.. _STIX-shifter: https://github.com/opencybersecurityalliance/stix-shifter
.. _Explore Kestrel huntbooks: http://github.com/opencybersecurityalliance/kestrel-huntbook
