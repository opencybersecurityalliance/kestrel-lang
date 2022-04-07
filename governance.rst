============================
Kestrel Language Development
============================

Semantic Versioning
-------------------

Before OCA TSC establishes versioning guideline for all OCA project, Kestrel language repo uses the following semantic versioning rules:

- A package is released with version *Major.Minor.Patch*.

- Major number: This should be incremented every time there is dramatic model change of the Kestrel language, e.g., `entity-based cyber reasoning`_ is established from ``v0`` to ``v1``, which rules how variables are defined/used, how pivoting between hunt steps, and how the composition of hunt-flow is performed.

- Minor number: This should be incremented every time important features are introduced, which can make backward incompatible changes to the language or interfaces, but not dramatically change the language with big new concepts. Examples:

  - A new feature realizes a new capability within the scope of the existing architecture or design concept, e.g., new analytics interface, it should be a new minor number.

  - A new command is added to syntax within the scope of existing architecture, e.g., ``CONFIG`` for dynamically updating configuration in a session, ``GENERATE REPORT`` to generate hunting report from the hunt-flow.

  - A dramatic improvement of the internal data model, e.g., `firepit`_ supports full entity-based graph schema.

- Patch number: This should be incremented every time small improvement features are added, bugs are fixed, and other small updates that do not change the language syntax or interface.

Release Procedure
-----------------

A maintainer can perform a release of a Kestrel package, e.g., ``kestrel-lang``, ``kestrel-jupyter`` following the procedure below:

1. Update version and changelog

    - Sync the local git repo to the latest of the ``develop`` branch.
    - Update the ``version`` field in ``setup.cfg``.
    - Add changes in ``CHANGELOG.rst`` under the new version section using the `Keep a Changelog`_ format.
    - Commit the updates with the new version number as the title.
    - Push the local ``develop`` branch to remote.
  
2. Graduate code to the ``release`` branch

    - Open a PR to merge the ``develop`` branch to the ``release`` branch. Use the version number as the PR title.

    - Merge the PR.
    
3. Create a new release

    - Go to the release page and click *Draft a new release*.
    
    - Type the version number as the new tag to create.
    
    - Choose ``release`` branch as the target.
    
    - Specify a release title. Use the version number as default.
    
    - Write a summary/highlight of the release. For patch number change, just copy the CHANGELOG entries. For Minor version change with lots of items, better to have a TLDR at the beginning highlighting the most important new feature.
    
    - Hit the *Publish release* button.
    
4. After release check

    - Check PyPI after a few minutes to confirm new package built and released.
    - May want to activate/pin the specific version of Kestrel documentation at `readthedocs version control`_.

.. _entity-based cyber reasoning: https://kestrel.readthedocs.io/en/latest/language.html#entity-based-reasoning
.. _firepit: https://github.com/opencybersecurityalliance/firepit
.. _Keep a Changelog: https://keepachangelog.com/en/1.0.0/
.. _readthedocs version control: https://readthedocs.org/projects/kestrel/versions/
