:orphan:

=====================
Kestrel Documentation
=====================

Kestrel documentation is automatically compiled and published to https://kestrel.readthedocs.io

To compile a local or offline copy:

.. code-block:: console

    $ pip install sphinx sphinx-rtd-theme
    $ make html

``autosectionlabel`` is enabled and refernces can be used:

- reference to a file: ``:doc:filePathRelativeToCurrentFile``

- reference to a section: ``:ref:topdir/dir/file:sectionTitle``

- reference to a section with text: ``:ref:text<topdir/dir/file:sectionTitle>``
