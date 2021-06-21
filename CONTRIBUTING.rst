============
Contributing
============

Contributions are welcome, and they are greatly appreciated!

You can contribute in many ways (more is coming):

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at `Kestrel issue tracker`_:

If you are reporting a bug, please include:

- Your operating system name and version.
- Any details about your local setup that might be helpful in troubleshooting.
- Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

We use the `Google Style`_ docstrings in our source code. Sphinx will pick them
up for documentation generation and publishing.

- `supported sections`_
- `docstring examples`_

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at `Kestrel issue tracker`_.

If you are proposing a feature:

- Explain in detail how it would work.
- Keep the scope as narrow as possible, to make it easier to implement.
- Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Code Style
----------

We follow the `symbol naming convention`_ and use `black`_ to format the code.

Development Workflow
--------------------

We follow the `branching model`_ summarized by Vincent Driessen.

In addition to the above model, we follow an additional branch naming rule:

- Branch name: ``feature-issueID-short-description``

  - prefix: either ``feature`` or ``hotfix``
  - issueID: a integer that refers to the issue with details
  - short-description: short description with hyphens as seperators

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated.
3. The pull request should work for Python 3.6 and 3.8.

.. _Kestrel issue tracker: https://github.com/opencybersecurityalliance/kestrel-lang/issues
.. _Symbol Naming Convention: https://google.github.io/styleguide/pyguide.html#3164-guidelines-derived-from-guidos-recommendations
.. _black: https://github.com/psf/black
.. _branching model: https://nvie.com/posts/a-successful-git-branching-model
.. _Google Style: https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings
.. _supported sections: https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html#docstring-sections
.. _docstring examples: https://www.sphinx-doc.org/en/master/usage/extensions/example_google.html
