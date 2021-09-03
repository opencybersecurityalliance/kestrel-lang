============
Installation
============

Install the Kestrel runtime plus additional front ends such as Kestrel Jupyter
Notebook kernel.

Operating Systems
=================

Currently, Kestrel is supported on Linux and macOS.

Requirements
============

Python
------

This project builds on Python 3. Refer to the `Python installation guide`_ if you do not have Python 3.

The preferred way to install Kestrel is with `pip`_. You must upgrade `pip`_ to the latest version before you install:

.. code-block:: console

    $ pip install --upgrade pip

SQLite
------

By default, Kestrel uses ``sqlite3`` as the storage back-end (more details in
`firepit`_ package), and ``firepit`` requires ``sqlite3 >= 3.24``. However,
``sqlite3`` is not a standalone Python package in Python 3, and Python version,
e.g., 3.6, is not coupled with ``sqlite3`` version, e.g., 3.22.

This means Python installer such as ``pip`` cannot resolve ``sqlite3`` version
requirement. You need manually run the following command in a terminal to check
your ``sqlite3`` version and upgrade ``sqlite3`` if needed.

.. code-block:: console

    $ sqlite3 --version

Among popular Linux distributions, the minimal distribution versions with
out-of-box Linux installations that satisfy the ``sqlite3`` version
requirement are:

- Archlinux
- Debian 10
- Fedora 33
- Gentoo
- openSUSE Leap 15.2
- RedHat 8
- Ubuntu 20.04 LTS

Runtime Installation
====================

You can install Kestrel runtime from `stable release`_ or `source code`_
(nightly built version). Either way installs all packages in the
``kestrel-lang`` repository, and dependent packages, such as `firepit`_ and
``stix-shifter``. See the architecture section in :doc:`overview` to understand
more.

It is a good practice to install Kestrel in a `Python virtual environment`_.
You can easily setup and activate one named *huntingspace*:

.. code-block:: console

    $ python -m venv huntingspace
    $ . huntingspace/bin/activate

Stable Release
--------------

Run this command in your terminal:

.. code-block:: console

    $ pip install kestrel-lang

Source Code (Nightly Built Version)
-----------------------------------

1. Install and upgrade Python building packages ``setuptools`` and ``wheel``:

.. code-block:: console

    $ pip install --upgrade pip setuptools wheel

2. Clone the source from the `Github repo`_:

.. code-block:: console

    $ git clone git://github.com/opencybersecurityalliance/kestrel-lang
    $ cd kestrel-lang

3. Install all packages from the repo:

.. code-block:: console

    $ pip install .

Runtime Front Ends
==================

Kestrel runtime currently supports three front ends (see architecture figure in :doc:`overview`):

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

    - Use `magic command`_ in iPython environment. ``kestrel-jupyter`` required.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/
.. _Python virtual environment: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/
.. _Github repo: https://github.com/opencybersecurityalliance/kestrel-lang
.. _kestrel-jupyter: http://github.com/opencybersecurityalliance/kestrel-jupyter
.. _Jupyter Notebook: https://jupyter.org/
.. _magic command: https://ipython.readthedocs.io/en/stable/interactive/magics.html
.. _firepit: https://github.com/opencybersecurityalliance/firepit
