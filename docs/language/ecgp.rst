==========================
Graph Pattern and Matching
==========================

This section describes *Extended Centered Graph Pattern* (ECGP), which goes
into the body of the ``WHERE`` clause in Kestrel :ref:`language/commands:GET`
and :ref:`language/commands:FIND` commands. This section also covers timestamp
formating and styling in Kestrel.

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

.. code-block:: coffeescript

    name = "powershell.exe"

Actually, this is called a *Comparison Expression*. In this case, a single
comparison expression constructs this simple pattern (ECGP).

Assuming the endpoint can be specified by a Kestrel data source
``stixshfiter://edp1`` and the `Time Range`_ is ``2022-11-11T15:05:00Z`` to
``2022-11-12T08:00:00Z``, we can put the pattern in the ``WHERE`` clause of the
command, and the entire ``GET`` command is:

.. code-block:: coffeescript

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

       .. code-block:: coffeescript

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

       .. code-block:: coffeescript

            name = 'powershell.exe'
            name = "powershell.exe"

    #. To be STIX pattern compatible, one can specify entity type before the
       attribute like ``entity_type:attribute``. For the simple powershell
       pattern, since the return entity type is already specified earlier in
       the ``GET`` command, this is redudant. However, this syntax is required
       for `Extended Centered Graph Pattern`_ where we will discuss more. In
       short, the following command returns exactly same results into ``ps3``
       as in ``ps``.

       .. code-block:: coffeescript

            ps3 = GET process
                  FROM stixshifter://edp1
                  WHERE process:name = 'powershell.exe'
                  START 2022-11-11T15:05:00Z STOP 2022-11-12T08:00:00Z

    #. To be STIX pattern compatible, one can put square brackets in the
       ``WHERE`` clause before the time range specification
       (``START``/``STOP``). That is to say, the following command returns
       exactly same results into ``ps4`` as in ``ps``.

       .. code-block:: coffeescript

            ps4 = GET process
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

Single Node Graph Pattern
=========================

Upgrading from specifying a single comparison expression to describing multiple
attributes of the returned entity in a pattern, one can use logical operators
``AND`` and ``OR`` to combine comparison expressions and use parenthesis ``()``
to specify the precedence of combined expressions. The result is a graph
pattern that has a single node---the returned entity.

Examples:

.. code-block:: coffeescript

    # a single (process) node graph pattern
    proc1 = GET process FROM stixshifter://edp1
            WHERE name = "powershell.exe" AND pid = 1234
            START 2022-11-11T15:05:00Z STOP 2022-11-12T08:00:00Z

    # a single (network-traffic) node graph pattern
    # this pattern is equivalent to `dst_port IN (80, 443)`
    netflow1 = GET network-traffic FROM stixshifter://gateway1
               WHERE dst_port = 80 OR dst_port = 443
               START 2022-11-11T15:05:00Z STOP 2022-11-12T08:00:00Z

    # a single (file) node graph pattern
    minikatz = GET file FROM stixshifter://edp1
               WHERE name = "C:\ProgramData\p.exe"
                  OR hashes.MD5 IN ( "1a4fe4413a92d478625d97b7df1bd0cf"
                                   , "b6ff8f31007a3629a3c4be8999001ec9"
                                   , "e8994399f1656e58f72443b8861ce5d1"
                                   , "9ae602fddb5d2f9b63c5eb6aad0a2612"
                                   )
               START 2022-11-11T15:05:00Z STOP 2022-11-12T08:00:00Z

    # a single (user-account) node graph pattern
    users = GET user-account FROM stixshifter://authlogs
            WHERE (user_id = 1001 AND account_login = "Tracy")
               OR  user_id = 0
               OR (user_id = 1003 AND is_privileged = true)
               OR (account_login = "JJ" AND is_privileged = true)
            START 2022-11-11T15:05:00Z STOP 2022-11-12T08:00:00Z


Centered Graph Pattern
======================

Extended Centered Graph Pattern
===============================

Referring to a Variable
=======================

``variable.attribute``

Escaped String
==============

Kestrel string literals in comparison expressions are like standard Python
strings (not Python raw string). It supports escaping for special characters,
e.g., ``\n`` means new line.

Some basic rules:

#. If double quotes are used to mark a string literal, any double quote
   character inside the string needs to be escaped. Otherwise, escaping for it
   is not necessary.

#. If single quotes are used to mark a string literal, any single quote
   character inside the string needs to be escaped. Otherwise, escaping for it
   is not necessary.

#. Backslash character ``\`` always needs to be escaped in a string literal,
   i.e., write ``\\`` to mean a single character ``\`` such as
   ``'C:\\Windows\\System32\\cmd.exe'``.

The 3rd rule means when writing regular expressions, one can first write a
regular expression in raw string, then replace each ``\`` with ``\\`` before
putting it into Kestrel.

Examples:

.. code-block:: coffeescript

    # the following will generate a STIX pattern
    # [process:command_line = 'powershell.exe "yes args"']
    pe1 = GET process FROM stixshifter://edp1
          WHERE command_line = "powershell.exe \"yes args\""

    # an easier way is to use single quote for string literal
    # when there are double quotes in the string
    # pe2 is the same as pe1
    pe2 = GET process FROM stixshifter://edp1
          WHERE command_line = 'powershell.exe "yes args"'

    # the following will generate a STIX pattern
    # [process:command_line = 'powershell.exe \'yes args\'']
    pe3 = GET process FROM stixshifter://edp1
          WHERE command_line = "powershell.exe 'yes args'"

    # backslash always needs to be escaped
    pe4 = GET process FROM stixshifter://edp1
          WHERE command_line = "C:\\Windows\\System32\\cmd.exe"

    # `\.` is the dot character in regex
    # use `\\.` since `\` needs to be escaped
    ps5 = GET process FROM stixshifter://edp1
          WHERE name MATCHES 'cmd\\.exe'

    # another regex escaping example that uses `\w` and `\.`
    ps5 = GET process FROM stixshifter://edp1
          WHERE name MATCHES '\\w+\\.exe'

Time Range
==========

Both absolute and relative time ranges are supported in Kestrel (commands
:ref:`language/commands:GET` and :ref:`language/commands:FIND`).

Absolute Time Range
-------------------

Absolute time range is specified as ``START isotime STOP isotime`` where
``isotime`` is a string following the basic rules:

- `ISO 8601`_ format should be used.

- Both date and time are required. `ISO 8601`_ requires letter ``T`` between the two parts.

- UTC is the only timezone currently supported, which is indicated by the letter ``Z`` at the end.

- The time should be at least specified to *second*:

    - standard precision to *second*: ``2022-11-11T15:05:00Z``

    - sub-second support: ``2022-11-11T15:05:00.5Z``

    - millisecond support: ``2022-11-11T15:05:00.001Z``

    - microsecond support: ``2022-11-11T15:05:00.00001Z``

- Quoted or unquoted are both valid.

    - unquoted: ``2022-11-11T15:05:00Z``

    - single-quoted: ``'2022-11-11T15:05:00Z'``

    - double-quoted: ``"2022-11-11T15:05:00Z"``

- STIX compatible stylings:

    - standard STIX timestamp: ``t'2022-11-11T15:05:00Z'``

    - STIX variant (double quotes): ``t"2022-11-11T15:05:00Z"``

Relative Time Range
-------------------

Relative time range is specified as ``LAST int TIMEUNIT`` where ``TIMEUNIT``
are one of the keywords ``DAY``, ``HOUR``, ``MINUTE``, or ``SECOND``. When
executing, the parser will generate the absoluate time range using the system
time (where the Kestrel runtime executes) as the ``STOP`` time, and the
``START`` time goes back ``int`` ``TIMEUNIT`` according to the relative time
range specified.


.. _STIX pattern: http://docs.oasis-open.org/cti/stix/v2.0/stix-v2.0-part5-stix-patterning.html
.. _stix-shifter: https://github.com/opencybersecurityalliance/stix-shifter
.. _ISO 8601: https://en.wikipedia.org/wiki/ISO_8601
.. _PCRE: https://www.pcre.org/
