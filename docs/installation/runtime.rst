===============
Install Runtime
===============

Kestrel runs in a Python environment on Linux, macOS, or Windows. On Windows,
please use Python inside Windows Subsystem for Linux (WSL).

General Requirements
====================

Python 3.8 is required. Follow the `Python installation guide`_ to install or upgrade Python.

OS-specific Requirements
========================

.. tab-set::

    .. tab-item:: Linux

        If you are using following Linux distributions or newer, the requirement is
        already met:

        .. grid:: 4
            :margin: 0

            .. grid-item::

                - Alpine 3.6

            .. grid-item::

                - Archlinux

            .. grid-item::

                - Debian 10

            .. grid-item::
            
                - Fedora 33

            .. grid-item::
            
                - Gentoo

            .. grid-item::
            
                - openSUSE 15.2

            .. grid-item::
            
                - Ubuntu 20.04

            .. grid-item::

                - RedHat 8

        Otherwise, check the SQLite version in a terminal with command
        ``sqlite3 --version`` and upgrade ``sqlite3
        >= 3.24`` as needed, which is required by `firepit`_, a Kestrel
        dependency, with default config.

    .. tab-item:: macOS

        Full installation of `Xcode`_ is required, especially for Mac with
        Apple silicon (M1/M2/...).

        The basic ``xcode-select --install`` may not install Python header
        files, or set incorrect architecture argument for dependent package
        compilation, so the full installation of `Xcode`_ is required.

    .. tab-item:: Windows (WSL)

        Nothing needed.

Choose Where to Install
=======================

.. tab-set::

    .. tab-item:: In a Python Virtual Environment [Recommended]

        It is a good practice to install Kestrel in a `Python virtual
        environment`_ so there will be no dependency conflict with Python
        packages in the system, plus all dependencies will be the latest.

        To setup and activate a Python virtual environment named
        ``huntingspace``:

        .. code-block:: console

            $ python3 -m venv huntingspace
            $ . huntingspace/bin/activate
            $ pip install --upgrade pip setuptools wheel

    .. tab-item:: User-wide

        If you don't like `Python virtual environment`_ or think it is too
        complicated, you can directly install Kestrel under a user.

        There is nothing you need to do in this step besides opening a terminal
        under that user, or login to the remote host under that user.

        The downside is all Python packages under that user are in the same
        namespace. If Kestrel requires a specific version of a library package,
        and another application requires a different version of the same
        library package, that will cause a conflict (``pip`` in the next step
        will give a warning if happens).

    .. tab-item:: OS-wide

        It is not recommended to install Kestrel as system packages since the
        configurations of Kestrel is under the user who runs it. However, it is
        possible to install Kestrel as system package, just open a terminal and
        swtich to ``root`` as follows:

        .. code-block:: console

            $ sudo -i

Kestrel Runtime Installation
============================

Execute the command in the terminal you opened in the last step. If you use
`Python virtual environment`_, the virtual environment should be activated for
any newly opened terminal.

.. tab-set::

    .. tab-item:: Stable Version

        .. code-block:: console

            $ pip install kestrel-jupyter
            $ python -m kestrel_jupyter_kernel.setup

    .. tab-item:: Nightly Built

        .. code-block:: console

            $ git clone git://github.com/opencybersecurityalliance/kestrel-lang
            $ cd kestrel-lang
            $ packages=(kestrel_core kestrel_datasource_stixbundle kestrel_datasource_stixshifter kestrel_analytics_python kestrel_analytics_docker kestrel_jupyter)
            $ for package in ${packages[@]}; do pip install packages/$package; done
            $ python -m kestrel_jupyter_kernel.setup

Kestrel Front-Ends
==================

Kestrel runtime currently supports three front-ends
(:ref:`overview/index:Kestrel in a Nutshell`). Use the following command to
invoke any of them:

.. tab-set::

    .. tab-item:: Jupyter Notebook
        
        This is the most popular front-end for Kestrel and it provides an
        interactive way to develop :ref:`language/tac:Hunt Flow` and
        :ref:`language/tac:Huntbook`. Start the Jupyter Notebook and dive into
        :ref:`tutorial:Kestrel + Jupyter`:

        .. code-block:: console

            $ jupyter nbclassic

    .. tab-item:: Command-line Utility
        
        The ``kestrel`` command is designed for batch execution and hunting
        automation. Use it right away in a terminal:

        .. code-block:: console

            $ kestrel myfirsthuntflow.hf

        Check out the :ref:`tutorial:Hello World Hunt` for more information.

    .. tab-item:: Python API

        You can use/call Kestrel from any Python program.

        - Start a Kestrel session in Python directly. See more at :doc:`../source/kestrel.session`.

        - Use `magic command`_ in iPython environment. Check `kestrel-jupyter`_ package for usage.

What's to Do Next
=================

- :doc:`datasource`
- :doc:`analytics`
- `Kestrel Language Tutorial`_
- :doc:`../language/index`

.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/
.. _Python virtual environment: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/
.. _Xcode: https://developer.apple.com/xcode/
.. _kestrel-lang: http://github.com/opencybersecurityalliance/kestrel-lang
.. _kestrel-jupyter: http://github.com/opencybersecurityalliance/kestrel-jupyter
.. _firepit: http://github.com/opencybersecurityalliance/firepit
.. _Jupyter Notebook: https://jupyter.org/
.. _magic command: https://ipython.readthedocs.io/en/stable/interactive/magics.html
.. _STIX-shifter: https://github.com/opencybersecurityalliance/stix-shifter
.. _Kestrel Language Tutorial: https://mybinder.org/v2/gh/opencybersecurityalliance/kestrel-huntbook/HEAD?filepath=tutorial
