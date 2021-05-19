===============================
Kestrel Jupyter Notebook Kernel
===============================

.. image:: https://img.shields.io/pypi/v/kestrel-jupyter.svg
        :target: https://pypi.python.org/pypi/kestrel-jupyter

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black

This repository contains two Python packages:

- ``kestrel_jupyter_kernel``
- ``kestrel_ipython``

Python Requirement
==================

This project and docs build on Python 3.

Install and Setup
=================

The easy and preferred way:

.. code-block:: console

    $ pip install kestrel-jupyter
    $ python -m kestrel_jupyter_kernel.setup

If you want to install from source code:

.. code-block:: console

    $ git clone git://github.com/IBM/kestrel-jupyter
    $ cd kestrel-jupyter
    $ pip install .
    $ python -m kestrel_jupyter_kernel.setup

How to Use Kestrel Jupyter Notebook Kernel
==========================================

Start Jupyter with ``jupyter notebook`` and start a new notebook with kernel
``kestrel``.

Write your hello world hunt:

.. code-block::

    newvar = NEW process ["cmd.exe", "reg.exe"]
    DISP newvar

Check `Kestrel documentation`_ for more.

How to Use ipython Magic Function
=================================

.. code-block:: python

    import kestrel_ipython

Then you can write any code in single-line or multi-line Kestrel in Python:

.. code-block:: python

    %%kestrel
    newvar = NEW process ["cmd.exe", "reg.exe"]
    DISP newvar

Uninstall Kestrel Jupyter Kernel
================================

List all Jupyter kernels installed:

.. code-block:: console

    $ jupyter kernelspec list

Uninstall Kestrel kernel:

.. code-block:: console

    $ jupyter kernelspec uninstall kestrel

.. _Kestrel documentation: https://kestrel.readthedocs.io/
