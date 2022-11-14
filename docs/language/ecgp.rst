==========================
Graph Pattern and Matching
==========================

This section describes *Extended Centered Graph Pattern* (ECGP), which goes
into the body of the ``WHERE`` clause in Kestrel :ref:`language/commands:GET`
and :ref:`language/commands:FIND` commands.

*In a nutshell, ECGP describes a forest with one of the trees named the centered
(sub-)graph and other trees as extended (sub-)graphs.*

ECGP is a superset of `STIX pattern`_, which means one can directly write a
STIX pattern in the ``WHERE`` clause. ECGP gives semantic explanation of
standard STIX pattern, a.k.a., `Centered Graph Pattern`_, and goes a little
beyond it for simplicity and expressiveness. This section explains ECGP from
its simplest form to its full power in the following subsections.

Single Comparison Expression Pattern
====================================

Kestrel implements :ref:`language/tac:Entity-Based Reasoning`, so the simplest
task to perform with Kestrel is to :ref:`language/commands:GET` entities
according to one of their attributes. For example, one may want to get all
``powershell.exe`` processes executed on a monitored endpoint during a time
range. The pattern is very simple:

.. code-block:: elixir

    name = "powershell.exe"

Actually, this is called a *Comparison Expression*. In this case, a single
comparison expression constructs this simple pattern (ECGP).

Assuming the endpoint can be specified by a Kestrel data source
``stixshfiter://edp1`` and the time range (in `ISO 8601`_ format) is
``2022-11-11T15:05:00Z`` to ``2022-11-12T08:00:00Z``, we can put the pattern in
the ``WHERE`` clause of the command, and the entire ``GET`` command is:

.. code-block:: elixir

    ps = GET process
         FROM stixshifter://edp1
         WHERE name = "powershell.exe"
         START 2022-11-11T15:05:00Z STOP 2022-11-12T08:00:00Z

Kestrel supports multiple stylings of writing a comparison expression:

    #. The command can be written in one or multiple lines with *any
       indentation style*. And the pattern itself can be written in one or
       multiple lines, which means either of the following is valid and the
       variable ``ps`` has the same entities as the following ``ps1`` and
       ``ps2``:

       .. code-block:: elixir

            ps1 = GET process FROM stixshifter://edp1 WHERE name = "powershell.exe"
                  START 2022-11-11T15:05:00Z STOP 2022-11-12T08:00:00Z

            ps2 = GET process
              FROM stixshifter://edp1
                        WHERE name =
              "powershell.exe"
                    START 2022-11-11T15:05:00Z
                STOP 2022-11-12T08:00:00Z

    #. One can use either single or double quotes around string literals, which
       means the following patterns are equivalent:

       .. code-block:: elixir

            name = 'powershell.exe'
            name = "powershell.exe"

    #. To be STIX pattern compatible, one can specify entity type before the
       attribute like ``entity_type:attribute``. For the simple powershell
       pattern, since the return entity type is already specified earlier in
       the ``GET`` command, this is redudant. However, this syntax is required
       for `Extended Centered Graph Pattern`_ where we will discuss more. In
       short, the following command returns exactly same results into ``ps3``
       as in ``ps``.

       .. code-block:: elixir

            ps3 = GET process
                  FROM stixshifter://edp1
                  WHERE process:name = 'powershell.exe'
                  START 2022-11-11T15:05:00Z STOP 2022-11-12T08:00:00Z

    #. To be STIX pattern compatible, one can put square brackets in the
       ``WHERE`` clause before the time range specification
       (``START``/``STOP``). The following are equivalent to ``ps``:

       .. code-block:: elixir

            ps4 = GET process
                  FROM stixshifter://edp1
                  WHERE [name = 'powershell.exe']
                  START 2022-11-11T15:05:00Z STOP 2022-11-12T08:00:00Z

            ps5 = GET process
                  FROM stixshifter://edp1
                  WHERE [process:name = 'powershell.exe']
                  START 2022-11-11T15:05:00Z STOP 2022-11-12T08:00:00Z

Kestrel supports three types of values in comparison expressions: a literal string, a
number, or a list (or nested list). For examples:

    - Number as value: ``src_port = 3389``

    - List as value: ``name IN ('bash', 'csh', "zsh", 'sh')``

    - Square bracket around list: ``dst_port IN [80, 443, 8000, 8888]``

    - Nested list support (flattened after parsing): ``name IN ('bash', ('csh', ('zsh')), "sh")``

Kestrel supports the following operators in comparison expression (yet a
specific stix-shifter connecotr may currently supports a subset of these):

    - ``=``/``==``: They are the same.

    - ``>``/``>=``/``<``/``<=``: They work for number as a value.

    - ``!=``/``NOT``: The negative operator.

    - ``IN``: To be followed by a list or a nested list.

    - ``LIKE``: To be followed by a quoted string with wildcard ``%`` (as defined in SQL).

    - ``MATCHES``: To be followed by a quoted string of Regular Expression (`PCRE`_).

    - ``ISSUBSET``: Only used for deciding if an IP address/subnet is in a
      subnet, e.g., ``ipv4-addr:value ISSUBSET '198.51.100.0/24'``. Details in
      `STIX pattern`_.

    - ``ISSUPERSET``: Only used for deciding if an IP subnet is larger than
      another subnet/IP, e.g., ``ipv4-addr:value ISSUPERSET
      '198.51.100.0/24'``. Details in `STIX pattern`_.

Regarding timestamp, the following stylings are supported/equivalent:

    - unquoted: ``2022-11-11T15:05:00Z``

    - single-quoted: ``'2022-11-11T15:05:00Z'``

    - double-quoted: ``"2022-11-11T15:05:00Z"``

    - STIX-compatible: ``t'2022-11-11T15:05:00Z'``

    - STIX-compatible (variant): ``t"2022-11-11T15:05:00Z"``

    - sub-second support: ``2022-11-11T15:05:00.5Z``

    - millisecond support: ``2022-11-11T15:05:00.001Z``

    - microsecond support: ``2022-11-11T15:05:00.00001Z``

Single Node Graph Pattern
=========================

Centered Graph Pattern
======================

Extended Centered Graph Pattern
===============================

Referring to a Variable
=======================

``variable.attribute``



.. _STIX pattern: http://docs.oasis-open.org/cti/stix/v2.0/stix-v2.0-part5-stix-patterning.html
.. _stix-shifter: https://github.com/opencybersecurityalliance/stix-shifter
.. _ISO 8601: https://en.wikipedia.org/wiki/ISO_8601
.. _PCRE: https://www.pcre.org/
