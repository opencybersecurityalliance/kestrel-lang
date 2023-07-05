.. image:: https://github.com/opencybersecurityalliance/kestrel-lang/raw/develop/logo/logo_w_text.svg
   :width: 432
   :alt: Kestrel Threat Hunting Language

.. image:: https://img.shields.io/pypi/pyversions/kestrel-lang
        :target: https://www.python.org/
        :alt: Python 3

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
        :target: https://github.com/psf/black
        :alt: Code Style: Black

.. image:: https://codecov.io/gh/opencybersecurityalliance/kestrel-lang/branch/develop/graph/badge.svg?token=HM4ax10IW3
        :target: https://codecov.io/gh/opencybersecurityalliance/kestrel-lang
        :alt: Code Coverage

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

**[News]** Kestrel session at `Black Hat USA 2023`_

--------

Kestrel is a threat hunting language aiming to make cyber threat hunting *fast*
by providing a layer of abstraction to build reusable, composable, and
shareable hunt-flow. Starting with:

#. `Black Hat USA 2022 session recording`_
#. `Black Hat USA 2022 Kestrel hunting lab`_
#. `Kestrel live tutorial in a cloud sandbox`_

The Goal
========

Software developers write Python or Swift than machine code to quickly turn
business logic into applications. Threat hunters write Kestrel to quickly turn
threat hypotheses into hunt-flow. We see threat hunting as an interactive
procedure to create customized intrusion detection systems on the fly, and
hunt-flow is to hunts as control-flow is to ordinary programs.

What does it mean by *hunt fast*?

- Do NOT write the same TTP pattern in different data source queries.
- Do NOT write one-time-use adapaters to connect hunt steps.
- Do NOT waste your existing analytic scripts/programs in future hunts.
- DD construct your hunt-flow from smaller reuseable hunt-flow.
- Do share your huntbook with your future self and your colleagues.
- Do get interactive feedback and revise hunt-flow on the fly.

|

.. image:: https://github.com/opencybersecurityalliance/data-bucket-kestrel/raw/main/images/github_homepage_animation.gif
   :width: 90%
   :target: https://www.youtube.com/watch?v=tASFWZfD7l8
   :alt: Kestrel Hunting Demo

Kestrel in a Nutshell
=====================

.. image:: https://github.com/opencybersecurityalliance/kestrel-lang/raw/develop/docs/images/overview.png
   :width: 100%
   :alt: Kestrel overview.

- **Kestrel language**: a threat hunting language for a human to express *what to
  hunt*.

  - expressing the knowledge of *what* in patterns, analytics, and hunt flows.
  - composing reusable hunting flows from individual hunting steps.
  - reasoning with human-friendly entity-based data representation abstraction.
  - thinking across heterogeneous data and threat intelligence sources.
  - applying existing public and proprietary detection logic as analytic hunt steps.
  - reusing and sharing individual hunting steps, hunt-flow, and entire huntbooks.

- **Kestrel runtime**: a machine interpreter that deals with *how to hunt*.

  - compiling the *what* against specific hunting platform instructions.
  - executing the compiled code locally and remotely.
  - assembling raw logs and records into entities for entity-based reasoning.
  - caching intermediate data and related records for fast response.
  - prefetching related logs and records for link construction between entities.
  - defining extensible interfaces for data sources and analytics execution.

Basic Concepts and Howto
========================

Visit `Kestrel documentation`_ to learn Kestrel:

- Learn concepts and syntax:

  - `A comprehensive introduction to Kestrel`_
  - `The two key concepts of Kestrel`_
  - `Interactive tutorial with quiz`_
  - `Language reference book`_

- Hunt in your environment:

  - `Kestrel runtime installation`_
  - `How to connect to your data sources`_
  - `How to execute an analytic hunt step in Python/Docker`_
  - `How to use Kestrel via API`_

Kestrel Huntbooks And Analytics
===============================

- `Kestrel huntbook`_: community-contributed Kestrel huntbooks
- `Kestrel analytics`_: community-contributed Kestrel analytics

Kestrel Hunting Blogs
=====================

#. `Building a Huntbook to Discover Persistent Threats from Scheduled Windows Tasks`_
#. `Practicing Backward And Forward Tracking Hunts on A Windows Host`_
#. `Building Your Own Kestrel Analytics and Sharing With the Community`_
#. `Setting Up The Open Hunting Stack in Hybrid Cloud With Kestrel and SysFlow`_
#. `Try Kestrel in a Cloud Sandbox`_
#. `Fun with securitydatasets.com and the Kestrel PowerShell Deobfuscator`_

Talks And Demos
===============

Talk summary (visit `Kestrel documentation on talks`_ to learn details):

- 2023/08 `Black Hat USA 2023`_
- 2022/12 `Infosec Jupyterthon 2022`_ [`IJ'22 live hunt recording`_]
- 2022/08 `Black Hat USA 2022`_ [`BH'22 recording`_ | `BH'22 hunting lab`_]
- 2022/06 `Cybersecurity Automation Workshop`_
- 2022/04 `SC eSummit on Threat Hunting & Offense Security`_ (free to register/playback)
- 2021/12 `Infosec Jupyterthon 2021`_ [`IJ'21 live hunt recording`_]
- 2021/11 `BlackHat Europe 2021`_
- 2021/10 `SANS Threat Hunting Summit 2021`_: [`SANS'21 session recording`_]
- 2021/05 `RSA Conference 2021`_: [`RSA'21 session recording`_]

Connecting With The Community
=============================

- Join Kestrel slack channel:
  
  - Get a `slack invitation`_ to join `Open Cybersecurity Alliance workspace`_
  
    .. image:: https://opencyberallia.wpengine.com/wp-content/uploads/2022/03/OCA-logo-e1646689234325.png
       :width: 20%
       :alt: OCA logo
     
  - Join the *kestrel* channel to ask questions and connect with other hunters
  
- Contribute to the language development (`Apache License 2.0`_):

  - Create a `GitHub Issue`_ to report bugs and suggest new features
  - Follow the `contributing guideline`_ to submit your pull request
  - Refer to the `governance documentation`_ regarding PR merge, release, and vulnerability disclosure

- Share your huntbook and analytics:

  - `Kestrel huntbook`_
  - `Kestrel analytics`_




.. _Kestrel live tutorial in a cloud sandbox: https://mybinder.org/v2/gh/opencybersecurityalliance/kestrel-huntbook/HEAD?filepath=tutorial
.. _Kestrel documentation: https://kestrel.readthedocs.io/

.. _A comprehensive introduction to Kestrel: https://kestrel.readthedocs.io/en/stable/overview/
.. _The two key concepts of Kestrel: https://kestrel.readthedocs.io/en/stable/language/tac.html#key-concepts
.. _Interactive tutorial with quiz: https://mybinder.org/v2/gh/opencybersecurityalliance/kestrel-huntbook/HEAD?filepath=tutorial
.. _Kestrel runtime installation: https://kestrel.readthedocs.io/en/stable/installation/runtime.html
.. _How to connect to your data sources: https://kestrel.readthedocs.io/en/stable/installation/datasource.html
.. _How to execute an analytic hunt step in Python/Docker: https://kestrel.readthedocs.io/en/stable/installation/analytics.html
.. _Language reference book: https://kestrel.readthedocs.io/en/stable/language/commands.html
.. _How to use Kestrel via API: https://kestrel.readthedocs.io/en/stable/source/kestrel.session.html
.. _Kestrel documentation on talks: https://kestrel.readthedocs.io/en/stable/talks.html

.. _Kestrel huntbook: https://github.com/opencybersecurityalliance/kestrel-huntbook
.. _Kestrel analytics: https://github.com/opencybersecurityalliance/kestrel-analytics

.. _Building a Huntbook to Discover Persistent Threats from Scheduled Windows Tasks: https://opencybersecurityalliance.org/huntbook-persistent-threat-discovery-kestrel/
.. _Practicing Backward And Forward Tracking Hunts on A Windows Host: https://opencybersecurityalliance.org/backward-and-forward-tracking-hunts-on-a-windows-host/
.. _Building Your Own Kestrel Analytics and Sharing With the Community: https://opencybersecurityalliance.org/kestrel-custom-analytics/
.. _Setting Up The Open Hunting Stack in Hybrid Cloud With Kestrel and SysFlow: https://opencybersecurityalliance.org/kestrel-sysflow-open-hunting-stack/
.. _Try Kestrel in a Cloud Sandbox: https://opencybersecurityalliance.org/try-kestrel-in-a-cloud-sandbox/
.. _Fun with securitydatasets.com and the Kestrel PowerShell Deobfuscator: https://opencybersecurityalliance.org/fun-with-securitydatasets-com-and-the-kestrel-powershell-deobfuscator/

.. _RSA Conference 2021: https://www.rsaconference.com/Library/presentation/USA/2021/The%20Game%20of%20Cyber%20Threat%20Hunting%20The%20Return%20of%20the%20Fun
.. _RSA'21 session recording: https://www.youtube.com/watch?v=-Xb086R0JTk
.. _SANS Threat Hunting Summit 2021: https://www.sans.org/blog/a-visual-summary-of-sans-threat-hunting-summit-2021/
.. _SANS'21 session recording: https://www.youtube.com/watch?v=gyY5DAWLwT0
.. _BlackHat Europe 2021: https://www.blackhat.com/eu-21/arsenal/schedule/index.html#an-open-stack-for-threat-hunting-in-hybrid-cloud-with-connected-observability-25112
.. _Infosec Jupyterthon 2021: https://infosecjupyterthon.com/2021/agenda.html
.. _IJ'21 live hunt recording: https://www.youtube.com/embed/nMnHBnYfIaI?start=20557&end=22695
.. _Infosec Jupyterthon 2022: https://infosecjupyterthon.com/2022/agenda.html
.. _IJ'22 live hunt recording: https://www.youtube.com/embed/8Mw1yyYkeqM?start=23586&end=26545
.. _SC eSummit on Threat Hunting & Offense Security: https://www.scmagazine.com/esummit/automating-the-hunt-for-advanced-threats
.. _Cybersecurity Automation Workshop: http://www.cybersecurityautomationworkshop.org/
.. _Black Hat USA 2023: https://www.blackhat.com/us-23/arsenal/schedule/index.html#identity-threat-hunting-with-kestrel-33662
.. _Black Hat USA 2022: https://www.blackhat.com/us-22/arsenal/schedule/index.html#streamlining-and-automating-threat-hunting-with-kestrel-28014
.. _BH'22 recording: https://www.youtube.com/watch?v=tf1VLIpFefs
.. _Black Hat USA 2022 session recording: https://www.youtube.com/watch?v=tf1VLIpFefs
.. _BH'22 hunting lab: https://mybinder.org/v2/gh/opencybersecurityalliance/black-hat-us-2022/HEAD?filepath=demo
.. _Black Hat USA 2022 Kestrel hunting lab: https://mybinder.org/v2/gh/opencybersecurityalliance/black-hat-us-2022/HEAD?filepath=demo

.. _slack invitation: https://join.slack.com/t/open-cybersecurity/shared_invite/zt-19pliofsm-L7eSSB8yzABM2Pls1nS12w
.. _Open Cybersecurity Alliance workspace: https://open-cybersecurity.slack.com/
.. _GitHub Issue: https://github.com/opencybersecurityalliance/kestrel-lang/issues
.. _contributing guideline: CONTRIBUTING.rst
.. _governance documentation: GOVERNANCE.rst
.. _Apache License 2.0: LICENSE.md
