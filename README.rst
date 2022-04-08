.. image:: https://raw.githubusercontent.com/opencybersecurityalliance/kestrel-lang/develop/logo/logo_w_text.svg
   :width: 50%
   :alt: Kestrel Threat Hunting Language

.. image:: https://img.shields.io/pypi/pyversions/kestrel-lang
        :target: https://www.python.org/
        :alt: Python 3

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
        :target: https://github.com/psf/black
        :alt: Code Style: Black

.. image:: https://img.shields.io/pypi/v/kestrel-lang
        :target: https://pypi.python.org/pypi/kestrel-lang
        :alt: Latest Version

.. image:: https://img.shields.io/pypi/dm/kestrel-lang
        :target: https://pypistats.org/packages/kestrel-lang
        :alt: PyPI Downloads

.. image:: https://readthedocs.org/projects/kestrel/badge/?version=latest
        :target: https://kestrel.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

|

Kestrel is a threat hunting language aiming to make cyber threat hunting *fast*
by providing a layer of abstraction to build reusable, composable, and
shareable hunt-flow.

`Try Kestrel in a cloud sandbox without install`_.

Software developers write Python or Swift than machine code to quickly turn
business logic into applications. Threat hunters write Kestrel to quickly turn
threat hypotheses into hunt-flow. We see threat hunting as an interactive
procedure to create customized intrusion detection systems on the fly, and
hunt-flow is to hunts as control-flow is to ordinary programs.

What does it mean by *hunt fast*?

- Do not write the same TTP pattern against different data sources.
- Do not write customized adapaters to connect hunt steps.
- Do not waste your existing analytic scripts/programs in future hunts.
- Do construct your hunt-flow with smaller reuseable hunt-flow.
- Do share your hunt book with your future self and your colleagues.
- Do get interactive feedback and revise hunt-flow on the fly.

|

.. image:: https://github.com/opencybersecurityalliance/data-bucket-kestrel/raw/main/images/github_homepage_animation.gif
   :width: 80%
   :target: https://www.youtube.com/watch?v=tASFWZfD7l8
   :alt: Kestrel Hunting Demo

Kestrel in a Nutshell
=====================

.. image:: https://raw.githubusercontent.com/opencybersecurityalliance/kestrel-lang/release/docs/images/overview.png
   :width: 100%
   :alt: Kestrel overview.

- **Kestrel language**: a threat hunting language for a human to express *what to
  hunt*.

  - expressing the knowledge of *what* in patterns, analytics, and hunt flows.
  - composing reusable hunting flows from individual hunting steps.
  - reasoning with human-friendly entity-based data representation abstraction.
  - thinking across heterogeneous data and threat intelligence sources.
  - applying existing public and proprietary detection logic as analytic hunt steps.
  - reusing and sharing individual hunting steps, hunt-flow, and entire hunt books.

- **Kestrel runtime**: a machine interpreter that deals with *how to hunt*.

  - compiling the *what* against specific hunting platform instructions.
  - executing the compiled code locally and remotely.
  - assembling raw logs and records into entities for entity-based reasoning.
  - caching intermediate data and related records for fast response.
  - prefetching related logs and records for link construction between entities.
  - defining extensible interfaces for data sources and analytics execution.

Basic Concepts and Howto
========================

Some common topics/questions described in `Kestrel documentation`_:

- `A comprehensive introduction to Kestrel`_
- `Interactive tutorial with quiz`_
- `Kestrel runtime installation`_
- `How to connect to your data sources`_
- `How to execute an analytic hunt step in Python/Docker`_
- `Language reference book`_
- `How to use Kestrel via API`_

Kestrel Hunt Books And Analytics
================================

- `Kestrel huntbook`_: community-contributed Kestrel huntbooks
- `Kestrel analytics`_: community-contributed Kestrel analytics

Kestrel Hunting Blogs
=====================

#. `Building a Huntbook to Discover Persistent Threats from Scheduled Windows Tasks`_
#. `Practicing Backward And Forward Tracking Hunts on A Windows Host`_
#. `Building Your Own Kestrel Analytics and Sharing With the Community`_
#. `Setting Up The Open Hunting Stack in Hybrid Cloud With Kestrel and SysFlow`_

Talks And Demos
===============

- Apr 2022 `SC Media eSummit on Threat Hunting & Offense Security`_
- Dec 2021 `Infosec Jupyterthon 2021`_ `[live hunt recording]<https://www.youtube.com/embed/nMnHBnYfIaI?start=20557&end=22695>`_
- Nov 2021 `BlackHat Europe 2021`_
- Oct 2021 `SANS Threat Hunting Summit 2021`_: `[recording]<https://www.youtube.com/watch?v=gyY5DAWLwT0>`_
- May 2021 `RSA Conference 2021`_: `[session recording]<https://www.youtube.com/watch?v=-Xb086R0JTk>`_

Connecting With The Community
=============================

- Ask questions, give suggestions, and connect with other hunters using slack.
  
  - Get a `slack invitation`_ to join `Open Cybersecurity Alliance workspace`_
  - Join the *kestrel* channel to meet other hunters
  
- Contribute to the language development:

  - Create a GitHub issue to report bugs and new features
  - Follow the `contributing guideline`_ to submit your pull request

- Contribute to the hunting knowledge base:

  - `Kestrel huntbook`_
  - `Kestrel analytics`_

.. _Try Kestrel in a cloud sandbox without install: https://mybinder.org/v2/gh/opencybersecurityalliance/kestrel-huntbook/HEAD?filepath=tutorial
.. _Kestrel documentation: https://kestrel.readthedocs.io/
.. _A comprehensive introduction to Kestrel: https://kestrel.readthedocs.io/en/latest/overview.html
.. _Interactive tutorial with quiz: https://mybinder.org/v2/gh/opencybersecurityalliance/kestrel-huntbook/HEAD?filepath=tutorial
.. _Kestrel runtime installation: https://kestrel.readthedocs.io/en/latest/installation/runtime.html
.. _How to connect to your data sources: https://kestrel.readthedocs.io/en/latest/installation/datasource.html
.. _How to execute an analytic hunt step in Python/Docker: https://kestrel.readthedocs.io/en/latest/installation/analytics.html
.. _Language reference book: https://kestrel.readthedocs.io/en/latest/language.html
.. _How to use Kestrel via API: https://kestrel.readthedocs.io/en/latest/source/kestrel.session.html

.. _Kestrel huntbook: https://github.com/opencybersecurityalliance/kestrel-huntbook
.. _Kestrel analytics: https://github.com/opencybersecurityalliance/kestrel-analytics

.. _Building a Huntbook to Discover Persistent Threats from Scheduled Windows Tasks: https://opencybersecurityalliance.org/posts/kestrel-2021-07-26/
.. _Practicing Backward And Forward Tracking Hunts on A Windows Host: https://opencybersecurityalliance.org/posts/kestrel-2021-08-16/
.. _Building Your Own Kestrel Analytics and Sharing With the Community: https://opencybersecurityalliance.org/posts/kestrel-custom-analytics/
.. _Setting Up The Open Hunting Stack in Hybrid Cloud With Kestrel and SysFlow: https://opencybersecurityalliance.org/posts/kestrel-sysflow-bheu21-open-hunting-stack/

.. _RSA Conference 2021: https://www.rsaconference.com/Library/presentation/USA/2021/The%20Game%20of%20Cyber%20Threat%20Hunting%20The%20Return%20of%20the%20Fun
.. _SANS Threat Hunting Summit 2021: https://www.sans.org/blog/a-visual-summary-of-sans-threat-hunting-summit-2021/
.. _BlackHat Europe 2021: https://www.blackhat.com/eu-21/arsenal/schedule/index.html#an-open-stack-for-threat-hunting-in-hybrid-cloud-with-connected-observability-25112
.. _Infosec Jupyterthon 2021: https://infosecjupyterthon.com/2021/agenda.html
.. _SC Media eSummit on Threat Hunting & Offense Security: https://www.scmagazine.com/esummit/automating-the-hunt-for-advanced-threats

.. _slack invitation: https://docs.google.com/forms/d/1vEAqg9SKBF3UMtmbJJ9qqLarrXN5zeVG3_obedA3DKs/viewform?edit_requested=true
.. _Open Cybersecurity Alliance workspace: https://open-cybersecurity.slack.com/
.. _contributing guideline: CONTRIBUTING.rst
