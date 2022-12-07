===============================
Kestrel Jupyter Notebook Kernel
===============================

.. image:: https://img.shields.io/pypi/pyversions/kestrel-lang
        :target: https://www.python.org/
        :alt: Python 3
        
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
        :target: https://github.com/psf/black
        :alt: Code Style: Black

.. image:: https://codecov.io/gh/opencybersecurityalliance/kestrel-jupyter/branch/develop/graph/badge.svg?token=GUbeG7idna
        :target: https://codecov.io/gh/opencybersecurityalliance/kestrel-jupyter
        :alt: Code Coverage

.. image:: https://img.shields.io/pypi/v/kestrel-jupyter.svg
        :target: https://pypi.python.org/pypi/kestrel-jupyter
        :alt: Latest Version

This repository contains two Python packages:

- ``kestrel_jupyter_kernel``
- ``kestrel_ipython``

Install and Setup
=================

To install the released version:

.. code-block:: console

    $ pip install kestrel-jupyter
    $ python -m kestrel_jupyter_kernel.setup

To install the nightly built version:

.. code-block:: console

    $ git clone git://github.com/opencybersecurityalliance/kestrel-jupyter
    $ cd kestrel-jupyter
    $ pip install .
    $ python -m kestrel_jupyter_kernel.setup

How to Use Kestrel Jupyter Notebook Kernel
==========================================

Start Jupyter with ``jupyter nbclassic`` and start a new notebook with the
``kestrel`` kernel. Note if you are using ``jupyter lab``, most functionalities
are there such as code execution, error prompot, and context-aware
auto-complete, but the syntax highlighting is not ported from our Jupyter
Notebook environment to Jupyter Lab yet.

Write your hello world hunt:

.. code-block:: elixir

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

How to Contribute
=================

As a component in the Kestrel runtime, this repo follows the `contributing guideline`_ and `governance documentation`_ in the main `kestrel-lang`_ repo.

.. _contributing guideline: https://github.com/opencybersecurityalliance/kestrel-lang/blob/develop/CONTRIBUTING.rst
.. _governance documentation: https://github.com/opencybersecurityalliance/kestrel-lang/blob/develop/GOVERNANCE.rst
.. _kestrel-lang: https://github.com/opencybersecurityalliance/kestrel-lang
