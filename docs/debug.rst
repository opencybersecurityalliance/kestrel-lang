=====
Debug
=====

If you encountered a Kestrel error, you may want to ask for help in our `OCA
slack`_ channel of Kestrel. A Kestrel veteran may guide you to further dig out
the issue in Kestrel debug mode.

Kestrel Errors
==============

Generally there are two categories of Kestrel errors:

- Kestrel exceptions: the errors that have been thought by Kestrel developers
  and encapsulated in a Kestrel Exception class listed here:
  :doc:`source/kestrel.exceptions`. These errors can be quickly explained by a
  Kestrel developer and their root causes are limited.

- Generic Python exceptions: the errors that haven't been captured by Kestrel
  runtime, which may be due to the incomplete try/catch coverage in Kestrel
  code or an error from a third party code, e.g., a dependent library or a
  Kestrel analytics (e.g., :doc:`source/kestrel_analytics_python.interface`).
  These errors usually need further debug, especially help from you to work
  with a Kestrel or third party code developer to debug.

Enable Debug Mode
=================

You can run Kestrel in debug mode by either use the ``--debug`` flag of the
Kestrel command-line utility, or create environment variable ``KESTREL_DEBUG``
with any value before launching Kestrel, which is useful when you use Kestrel
in Jupyter Notebook. In the debug mode, all runtime data including caches and
logs at debug level are at ``/tmp/kestrel/``. The runtime logs of the latest
created session is at ``/tmp/kestrel/session.log``.

Add Your Own Log Entry
======================

If a Kestrel veteran assisted you in further debuging an issue, it is likely
he/she will let you add a debug log entry to a specific Kestrel module/function
to print out some value:

#. Clone the `kestrel-lang`_ repo:

    .. code-block:: console

        $ git clone https://github.com/opencybersecurityalliance/kestrel-lang.git

#. Ensure the following is in the module you'd like to debug (add if not):

    .. code-block:: python

        import logging
        _logger = logging.getLogger(__name__)

#. Add debug log entry where you want:

    .. code-block:: python

        _logger.debug(something_you_want_to_log)

#. Install your local Kestrel build:

    .. code-block:: console

        $ pip install .

#. Rerun Kestrel (command-line utility or restart Kestrel kernel in Jupyter)
   and check the entry you logged at ``/tmp/kestrel/session.log``.

.. _kestrel-lang: http://github.com/opencybersecurityalliance/kestrel-lang
.. _OCA slack: https://open-cybersecurity.slack.com/
