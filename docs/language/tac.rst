========================
Terminology and Concepts
========================

This section helps junior hunters understand basic hunting terminology and
align senior hunters with Kestrel's entity-based hunting methodology to focus
on *what to hunt* and hunt efficiently.

Basic Terminology
=================

Record
------

A record, log, or observation yielded by a host or network monitoring system.
Usually a record contains information of an activity that is worth recording.
For example:

    - An ssh login attempt with root
    - A user login and logout
    - A process forking another process
    - A network connection initialized by a process
    - A process loading a dynamic loaded library
    - A process reading a sensitive file

Formally defined, a record is a piece of machine-generated data that is part of
a telemetry of the monitored host or network. Different monitoring systems
yield records in their own formats and define the scope of a record
differently. A monitoring system may yield a record for each file a process
loaded, while another monitoring system may yield a record with a two- or
three-level process tree plus loaded binaries and dynamic libraries as
additional file nodes in the tree.

Entity
------

An entity is a system, network, or cyber object that can be identified by a
monitor. Different monitors may have different capabilities identifying
entities: an IDS can identify an IP or a host, while an EDR may identify a
process or a file inside the host.

A record yielded by a monitor contains one or more entities visible to the
monitor. For example:

    - A log of an ssh login attempt with root may contain three entities:
      the ssh process, the user root, and the incoming IP.
    - A web server, e.g., nginx, connection log entry may contain two
      entities: the incoming IP and the requested URL.
    - An EDR process tree record may contain several entities including the
      root process, its child processes, and maybe its grand child
      processes.
    - An IDS alert observation may contain two entities: the incoming IP
      and the target host.

Not only can a record contain multiple entities, but the same entity
identified by the same monitor may appear in different records. Some monitors
generate a universal identifier for an entity they track, i.e., UUID/GUID,
but this does not always hold. In addition, the description of an entity in a
record may be very incomplete due to the limited monitoring capability, data
aggregation, or software bug.

Hunt
----

A cyberthreat hunt is a procedure to find a set of entities in the monitored
environment that associates with a cyberthreat.

A comprehensive hunt or threat discovery finds a set of entities with their
relations, for example, control- and data-flows among them, as a graph that
associates with a cyberthreat. The comprehensive hunting definition assumes
fully connected telemetry data provided by monitoring systems and is discussed
in the :doc:`../theory`.

Hunt Step
---------

A step in a hunt usually performs one of the five types of hunting actions:

    #. Retrieval: *getting a set of entities*. The entities may be directly
       retrieved back from a monitor or a data lake with stored monitored
       data, or can be quickly picked up at any cache layer on the path
       from the user to a data source.

    #. Transformation: *deriving different forms of entities*. Within a basic
       entity type such as *network-traffic*, threat hunters can perform simple
       transformation such as sampling or aggregating them based on their
       attributes. The results are special *network-traffic* with aggregated
       fields.

    #. Enrichment: *adding information to a set of entities*. Computing
       attributes or labels for a set of entities and attach them to the
       entities. The attributes can be context such as domain name for an
       IP address. They can also be threat intelligence information or even
       detection labels from existing intrusion detection systems.

    #. Inspection: *showing information about a set of entities*. For
       example, listing all attributes an labels of a set of entities;
       showing values of specified attributes of a set of entities.

    #. Flow-control: *merge or split hunt flows*. For example, merge the
       results of two hunt flows to apply the same hunt steps afterwords, or to
       fork a hunt flow branch for developing a variant of the threat
       hypothesis.

Hunt Flow
---------

The control flow of a hunt. A hunt flow comprises a series of hunt steps,
computing multiple sets of entities, and deriving new sets of entities based on
previous ones. Finally, a hunt flow reveals all sets of entities that are
associated with a threat.

A hunt flow in Kestrel is a sequence of Kestrel commands. It can be stored in a
plain text file with suffix ``.hf`` and executed by Kestrel command line, e.g.,
``kestrel apt51.hf``.

Huntbook
--------

A hunt flow combined with its execution results in a notebook format. Usually
a saved Jupyter notebook of a Kestrel hunt is referred to as a huntbook, which
contains the hunt flow in blocks and its execution results displayed in text,
tables, graphs, and other multi-media forms.

Jupyter Notebook supports saving a huntbook (``*.ipynb``) into a hunt flow
(``*.hf``) by clicking ``File`` -> ``Download as`` -> ``Kestrel (.hf)``.

Key Concepts
============

Kestrel brings two key concepts to cyberthreat hunting.

Entity-Based Reasoning
----------------------

Humans understand threats and hunting upon entities, such as, malware,
malicious process, and C&C host. As a language for threat hunters to express
*what to hunt*, Kestrel helps hunters to organize their thoughts on threat
hypotheses around entities. To compute/compile *how to hunt*, the Kestrel
runtime assembles entities with pieces of information in different records that
describes different aspects of the entities, e.g., some events describe process
forking/spawning, and some other events describe network communications of the
same processes. Kestrel also proactively asks data sources to get information
about entities---the *prefetch* procedure in Kestrel. With this design, threat
hunters always have all of the information available about the entities they
are focusing on, and can confidently create and revise threat hypotheses based
on the entities and their connected entities. Meanwhile, threat hunters do not
need to spend time stitching and correlating records since most of this tedious
work on *how to hunt* is solved by Kestrel runtime.

Composable Hunt Flow
--------------------

Simplicity is the design goal of Kestrel, yet Kestrel does not sacrifice the
power of hunting. The secret sauce to achieve both is the idea of composability
from functional programming.

To compose hunt flows freely, Kestrel defines a common data model around
entities, that is, Kestrel variables, as the input and output of every hunt
step. Every hunt step yields a Kestrel variable (or ``None``), which can be
the input of another hunt step. In addition to freely pipe hunt steps to
compose hunt flows, Kestrel also enables hunt flows forking and merging:

    - To fork a hunt flow, just consume the same Kestrel variable by another
      hunt step.
    - To merge hunt flows, just do a hunt step that takes in multiple Kestrel
      variables.

Here's an example of a composable Kestrel hunt flow:

.. image:: ../images/huntflow.png
   :width: 100%
   :alt: An example of composable Kestrel hunt flow.
