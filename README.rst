===============================
Kestrel Threat Hunting Language
===============================

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

.. image:: https://raw.githubusercontent.com/subbyte/kestrel-gif/main/hunt01.gif
   :width: 100%
   :target: https://www.youtube.com/watch?v=tASFWZfD7l8
   :alt: Kestrel Hunting Demo

Overview
========

Kestrel threat hunting language provides an abstraction for threat hunters to
focus on *what to hunt* instead of *how to hunt*. The abstraction makes it
possible to codify resuable hunting knowledge in a composable and sharable
manner. And Kestrel runtime figures out *how to hunt* for hunters to make cyber
threat hunting less tedious and more efficient.

.. image:: https://raw.githubusercontent.com/opencybersecurityalliance/kestrel-lang/release/docs/images/overview.png
   :width: 100%
   :alt: Kestrel overview.

- **Kestrel language**: a threat hunting language for a human to express *what to
  hunt*.

  - expressing the knowledge of *what* in patterns, analytics, and hunt flows.
  - composing reusable hunting flows from individual hunting steps.
  - reasoning with human-friendly entity-based data representation abstraction.
  - thinking across heterogeneous data and threat intelligence sources.
  - applying existing public and proprietary detection logic as analytics.
  - reusing and sharing individual hunting steps and entire hunt books.

- **Kestrel runtime**: a machine interpreter that deals with *how to hunt*.

  - compiling the *what* against specific hunting platform instructions.
  - executing the compiled code locally and remotely.
  - assembling raw logs and records into entities for entity-based reasoning.
  - caching intermediate data and related records for fast response.
  - prefetching related logs and records for link construction between entities.
  - defining extensible interfaces for data sources and analytics execution.

Installation
============

Kestrel requires Python 3.x to run. Check `Python installation guide`_ if you
do not have Python. It is preferred to install Kestrel runtime using `pip`_,
and it is preferred to install Kestrel runtime in a `Python virtual
environment`_.

0. Update Python installer.

.. code-block:: console

    $ pip install --upgrade pip setuptools wheel

1. Install Kestrel runtime.

.. code-block:: console

    $ pip install kestrel-lang

2. Install Kestrel Jupyter kernel if you use `Jupyter Notebook`_ to hunt.

.. code-block:: console

    $ pip install kestrel-jupyter
    $ python -m kestrel_jupyter_kernel.setup

3. (Optional) download Kestrel analytics examples for the ``APPLY`` hunt steps.

.. code-block:: console

    $ git clone https://github.com/opencybersecurityalliance/kestrel-analytics.git

Hello World Hunt
================

1. Copy the following 3-step hunt flow into your favorite text editor:

.. code-block::

    # create four process entities in Kestrel and store them in the variable `proclist`
    proclist = NEW process [ {"name": "cmd.exe", "pid": "123"}
                           , {"name": "explorer.exe", "pid": "99"}
                           , {"name": "firefox.exe", "pid": "201"}
                           , {"name": "chrome.exe", "pid": "205"}
                           ]

    # match a pattern of browser processes, and put the matched entities in variable `browsers`
    browsers = GET process FROM proclist WHERE [process:name IN ('firefox.exe', 'chrome.exe')]

    # display the information (attributes name, pid) of the entities in variable `browsers`
    DISP browsers ATTR name, pid

2. Save to a file ``helloworld.hf``.

3. Execute the hunt flow in a terminal (in Python venv if virtual environment is used):

.. code-block:: console

    $ kestrel helloworld.hf

Now you captured browser processes in a Kestrel variable ``browsers`` from all processes created:

::
    
           name pid
     chrome.exe 205
    firefox.exe 201

    [SUMMARY] block executed in 1 seconds
    VARIABLE    TYPE  #(ENTITIES)  #(RECORDS)  process*
    proclist process            4           4         0
    browsers process            2           2         0
    *Number of related records cached.

Hunting In The Real World
=========================

#. How to develop hunts interactively in Jupyter Notebook?
#. How to connect to one and more real-world data sources?
#. How to write and match a TTP pattern?
#. How to find child processes of a process?
#. How to find network traffic from a process?
#. How to apply pre-built analytics?
#. How to fork and merge hunt flows?

Find more at `Kestrel documentation hub`_ and `Kestrel blogs at OCA`_.

Kestrel Hunting Blogs
=====================

#. `Building a Huntbook to Discover Persistent Threats from Scheduled Windows Tasks`_
#. `Practicing Backward And Forward Tracking Hunts on A Windows Host`_
#. `Building Your Own Kestrel Analytics and Sharing With the Community`_

Learning/Sharing With the Community
===================================

- `Kestrel huntbook repo`_
- `Kestrel analytics repo`_

Talks And Demos
===============

Kestrel was debuted at RSA Conference 2021 with its goal of an `efficient
cyberthreat hunting symbiosis`_, its key design concepts `entity-based
reasoning`_ and `composable hunt flow`_, as well as a small-enterprise APT
hunting demo with TTP pattern matching, cross-host provenance tracking,
TI-enrichment, machine learning analytics, and more. Watch our session `The
Game of Cyber Threat Hunting: The Return of the Fun`_ (30 minutes with demo) or
the `demo`_ alone (15 minutes).

Kestrel was further introduced to the threat hunting community at `SANS Threat
Hunting Summit 2021`_ in session `Compose Your Hunts With Reusable Knowledge
and Share Your Huntbook With the Community`_ to facilitate huntbook
composition, sharing, and reuse. The session started from 3 simple hunt step
demos---TTP pattern matching, provenance tracking, and data visualization
analytics---then went into comprehensive hunt flow composition to convey the
idea of hunting knowledge composition and reuse. The recording is currently
available at SANS library and will be published by SANS.

Kestrel will be presented as part of the open hunting stack for hybrid cloud in
Black Hat Europe Arsenal 2021 session: `An Open Stack for Threat Hunting in
Hybrid Cloud With Connected Observability`_. We will hunt an APT in a hybrid
cloud that is a variant of a typical supply chain attack yet implemented in a
more stealthy manner. The open stack consisting of Kestrel, `SysFlow`_, and
other open-source projects will be presented. 

Connecting With The Community
=============================

Quick questions? Like to meet other users? Want to contribute?

Get a `slack invitation`_ to `Open Cybersecurity
Alliance workspace`_ and join our *kestrel* channel.

.. _Kestrel documentation hub: https://kestrel.readthedocs.io/
.. _Kestrel blogs at OCA: https://opencybersecurityalliance.org/posts/
.. _pip: https://pip.pypa.io/
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/
.. _Python virtual environment: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/
.. _Jupyter Notebook: https://jupyter.org/
.. _slack invitation: https://docs.google.com/forms/d/1vEAqg9SKBF3UMtmbJJ9qqLarrXN5zeVG3_obedA3DKs/viewform?edit_requested=true
.. _Open Cybersecurity Alliance workspace: https://open-cybersecurity.slack.com/
.. _efficient cyberthreat hunting symbiosis: https://kestrel.readthedocs.io/en/latest/overview.html#human-machine
.. _demo: https://www.youtube.com/watch?v=tASFWZfD7l8
.. _entity-based reasoning: https://kestrel.readthedocs.io/en/latest/language.html#entity-based-reasoning
.. _composable hunt flow: https://kestrel.readthedocs.io/en/latest/language.html#composable-hunt-flow
.. _The Game of Cyber Threat Hunting\: The Return of the Fun: https://www.rsaconference.com/Library/presentation/USA/2021/The%20Game%20of%20Cyber%20Threat%20Hunting%20The%20Return%20of%20the%20Fun
.. _Building a Huntbook to Discover Persistent Threats from Scheduled Windows Tasks: https://opencybersecurityalliance.org/posts/kestrel-2021-07-26/
.. _Practicing Backward And Forward Tracking Hunts on A Windows Host: https://opencybersecurityalliance.org/posts/kestrel-2021-08-16/
.. _Building Your Own Kestrel Analytics and Sharing With the Community: https://opencybersecurityalliance.org/posts/kestrel-custom-analytics/
.. _Kestrel huntbook repo: https://github.com/opencybersecurityalliance/kestrel-huntbook
.. _Kestrel analytics repo: https://github.com/opencybersecurityalliance/kestrel-analytics
.. _SANS Threat Hunting Summit 2021: https://www.sans.org/cyber-security-summit/
.. _Compose Your Hunts With Reusable Knowledge and Share Your Huntbook With the Community: https://www.sans.org/blog/a-visual-summary-of-sans-threat-hunting-summit-2021/
.. _An Open Stack for Threat Hunting in Hybrid Cloud With Connected Observability: https://www.blackhat.com/eu-21/arsenal/schedule/index.html#an-open-stack-for-threat-hunting-in-hybrid-cloud-with-connected-observability-25112
.. _SysFlow: https://github.com/sysflow-telemetry
