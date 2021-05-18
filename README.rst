===============================
Kestrel Threat Hunting language
===============================

.. image:: https://img.shields.io/pypi/v/kestrel.svg
        :target: https://pypi.python.org/pypi/kestrel

.. image:: https://readthedocs.org/projects/kestrel/badge/?version=latest
        :target: https://kestrel.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black

This repository is the core library for Kestrel runtime.

It contains Python packages:

- ``kestrel``
- ``kestrel_datasource_stixbundle``
- ``kestrel_datasource_stixshifter``
- ``kestrel_analytics_docker``

Python Requirement
==================

This project and docs build on Python 3.

How to Use Kestrel
==================

All documents including Kestrel language and runtime information are published at ``readthedocs.io``.

To compile the latest documents locally:

.. code-block:: console

    $ git clone git://github.com/IBM/kestrel-lang
    $ cd kestrel-lang
    $ pip install .
    $ pip install sphinx sphinx-rtd-theme
    $ cd docs
    $ make html
    $ firefox _build/html/index.html
