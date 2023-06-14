============
Contributing
============

Contributions are welcome, and they are greatly appreciated!

Types of Contributions
----------------------

- Have something to say: join us at slack (find how to join in `README`_), or create a ticket at `GitHub Issues`_.

- Report bugs: report bugs at `GitHub Issues`_.

- Fix bugs: look through the `GitHub Issues`_ for bugs to fix.

- Implement features: look through the `GitHub Issues`_ for features to implement.

- Write documentation: we use the `Google Style`_ docstrings in our source code.

  - `supported sections`_
  - `docstring examples`_

- Share your Kestrel analytics: submit a PR to the `kestrel-analytics repo`_.

- Share your Kestrel huntbook: submit a PR to the `kestrel-huntbook repo`_.

Code Style
----------

We follow the `symbol naming convention`_ and use `black`_ to format the code.

How to Submit a Pull Request
----------------------------

Checklist before submitting a pull request:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated.
3. Run a full unittest with ``pytest``.
4. Check unused imports with ``unimport --check --exclude __init__.py src/``.
5. Black your code with ``black src/``.

All contributions must be covered by a `Contributor's License Agreement`_ (CLA) and ECLA (if you are contributing on behalf of your employer). You will get a prompt to sign CLA when you submit your first PR.

.. _GitHub Issues: https://github.com/opencybersecurityalliance/kestrel-lang/issues
.. _Symbol Naming Convention: https://google.github.io/styleguide/pyguide.html#3164-guidelines-derived-from-guidos-recommendations
.. _black: https://github.com/psf/black
.. _Google Style: https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings
.. _supported sections: https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html#docstring-sections
.. _docstring examples: https://www.sphinx-doc.org/en/master/usage/extensions/example_google.html
.. _README: README.rst
.. _kestrel-analytics repo: https://github.com/opencybersecurityalliance/kestrel-analytics
.. _kestrel-huntbook repo: https://github.com/opencybersecurityalliance/kestrel-huntbook
.. _Contributor's License Agreement: https://cla-assistant.io/opencybersecurityalliance/oasis-open-project
