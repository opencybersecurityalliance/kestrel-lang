Setup Kestrel Analytics
-----------------------

Kestrel analytics are one type of hunt steps (:ref:`language:APPLY`) that
provide foreign language interfaces to non-Kestrel hunting modules. You can
apply any external logic as a Kestrel analytics to

- compute new attributes to one or more Kestrel variables
- perform visualizations

Note Kestrel treats analytics as black boxes and only cares about the input and
output formats. So it is possible to wrap even proprietary software in a
Kestrel analytics to be a hunt step.

Kestrel Analytics Abstraction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Kestrel manages analytics in a two-level abstraction: an analytics registers at
a :doc:`../source/kestrel.analytics.interface`, which defines the way how a set
of analytics are executed and talk to Kestrel. In other words, Kestrel manages
multiple analytics interfaces at runtime, each of which manages a set of
analytics with the same execution model and input/output formats. Learn more
about the abstraction in :ref:`language:Data Source And Analytics Interfaces`.

Kestrel by default ships with the two most common analytics interfaces:

- :doc:`../source/kestrel_analytics_python.interface`

    - run a Python function as an analytics
    - require no additional software to run
    - simple and easy to write a new analytics
    - not limited to Python logic with process spawning support

- :doc:`../source/kestrel_analytics_docker.interface`

    - run a Docker container as an analytics
    - could pack any black-box logic in an analytics

Kestrel Analytics Repo
~~~~~~~~~~~~~~~~~~~~~~

Community-contributed Kestrel analytics are hosted at the `kestrel-analytics
repo`_, which support execution via either the Python or Docker analytics
interface. Currently there are Kestrel analytics for IP enrichment, threat
intelligence enrichment, machine learning inference, plotting, complex
visualization, clustering, suspicious process scoring, and log4shell
deobfuscation.

Clone the `kestrel-analytics repo`_ to start using existing open-sourced analytics:

.. code-block:: console

    $ git clone https://github.com/opencybersecurityalliance/kestrel-analytics.git

Setup Python Analytics
~~~~~~~~~~~~~~~~~~~~~~

The Python analytics interface calls a Kestrel analytics directly in Python, so
the interface is natively supported without any additional software. However,
you need to make sure the analytics function you are using is executable, e.g.,
all dependencies for the analytics have been installed.

To setup an analytics via the Python interface, you only need to tell Kestrel
where the analytics module/function is: specifying analytics profiles at
``~/.config/kestrel/pythonanalytics.yaml``. You can follow the `Kestrel
analytics example profile`_ in the `kestrel-analytics repo`_. To learn more
including how to write your own Python analytics, visit
:doc:`../source/kestrel_analytics_python.interface`.


Setup Docker Analytics
~~~~~~~~~~~~~~~~~~~~~~

To setup a Kestrel Docker analytics, you need to have `docker`_ installed, and
then build the docker container for that analytics. For example, to build a
docker container for the `Pin IP`_ analytics, go to its source code, download
``GeoLite2-City.mmdb`` as instructed in README, and run the command:

.. code-block:: console

    $ docker build -t kestrel-analytics-pinip .

To learn more about how to write and run a Kestrel analytics through the Docker
interface, visit :doc:`../source/kestrel_analytics_docker.interface` and our blog
`Building Your Own Kestrel Analytics`_.

What's to Do Next
~~~~~~~~~~~~~~~~~

- :ref:`tutorial:Run an Analytics`
- :ref:`language:APPLY`

.. _kestrel-analytics repo: https://github.com/opencybersecurityalliance/kestrel-analytics
.. _Kestrel analytics example profile: https://github.com/opencybersecurityalliance/kestrel-analytics/blob/release/pythonanalytics_sample.yaml
.. _docker: https://www.docker.com/
.. _Building Your Own Kestrel Analytics: https://opencybersecurityalliance.org/posts/kestrel-custom-analytics/
.. _Pin IP: https://github.com/opencybersecurityalliance/kestrel-analytics/tree/release/analytics/piniponmap
