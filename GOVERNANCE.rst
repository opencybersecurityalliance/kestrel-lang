============================
Kestrel Language Development
============================

Maintainers and Contributors
----------------------------

Find the current maintainers and contributors to the project at our `authors page`_.

GitHub Issue Management
-----------------------

Maintainers subscribe to the project and get notification of GitHub issue creation and updates. At least one maintainer needs to participate in a GitHub issue after created.

Code Contribution Management
----------------------------

Maintainers subscribe to the project and get notification of pull requests (PR). For bug fix PR, at least one maintainer needs to review and approve the PR before merging to the `develop` branch. For new feature PR, one maintainer will lead the discussion to review and merge it.

Branching Model
---------------

This repo generally follow the `branching model`_ summarized by Vincent Driessen. The two long-term branches are ``develop`` and ``release``.

Semantic Versioning
-------------------

Kestrel language repo uses the following semantic versioning rules before OCA-wide versioning guideline is established:

- A package is released with version *Major.Minor.Patch*.

- Major number: This should be incremented every time there is dramatic model change of the Kestrel language, e.g., `entity-based cyber reasoning`_ is established from ``v0`` to ``v1``, which rules how variables are defined/used, how to pivot between hunt steps, and how the composition of hunt-flow is performed.

- Minor number: This should be incremented every time important features are introduced, which could make *backward incompatible* changes to the language or interfaces, but not dramatically change the language model. Examples:

    - A new feature realizes a new capability within the scope of the existing architecture or design concept, e.g., new analytics interface, it should be a new minor number.

    - A new command is added to syntax within the scope of existing architecture, e.g., ``CONFIG`` for dynamically updating configuration in a session, ``GENERATE REPORT`` to generate hunting report from the hunt-flow.

    - A dramatic improvement of the internal data model, e.g., `firepit`_ supports full entity-based graph schema.

- Patch number: This should be incremented every time small improvement features are added, bugs are fixed, and other small updates that do not change the language syntax or interface.

Release Procedure
-----------------

A maintainer should release a new Kestrel runtime (PyPI package name: ``kestre-lang``) following the procedure:

1. Update version and changelog

    - Sync the local git repo to the latest of the ``develop`` branch.
    - Update the ``version`` field in ``setup.cfg``.
    - Add changes in ``CHANGELOG.rst`` under a new version section.
    - Add new contributors to ``AUTHORS.rst`` if any.
    - Commit the updates with the new version number as the message.
    - Push the local ``develop`` branch to remote.

2. Graduate code to the ``release`` branch

    - Open a PR to merge the ``develop`` branch to the ``release`` branch. Use the version number as the PR title.

    - Merge the PR.

3. Create a new release

    - Go to the release page and click *Draft a new release*.

    - Type the version number as the new tag to create.

    - Choose ``release`` branch as the *Target*.

    - Specify a release title. Use the version number for ordinary release.

    - Write a summary of the release.

        - Patch number release: copy the CHANGELOG entries.

        - Minor number release: may have a TLDR at the beginning highlighting the most important new feature.

    - Hit the *Publish release* button.

4. After release check

    - Check `kestrel-lang on PyPI`_ after a few minutes to confirm new package built and released.
    - May activate/pin the released version of Kestrel documentation at `readthedocs version control`_.

Vulnerability Disclosure
------------------------

In the case of a vulnerability, please contact any of the maintainers via slack to resolve the vulnerability as soon as possible (before or after it is published). To join OCA slack workspace, please follow the instructions in the `README`_.



.. _authors page: AUTHORS.rst
.. _branching model: https://nvie.com/posts/a-successful-git-branching-model
.. _entity-based cyber reasoning: https://kestrel.readthedocs.io/en/latest/language.html#entity-based-reasoning
.. _firepit: https://github.com/opencybersecurityalliance/firepit
.. _kestrel-lang on PyPI: https://pypi.org/project/kestrel-lang/
.. _readthedocs version control: https://readthedocs.org/projects/kestrel/versions/
.. _README: README.rst
