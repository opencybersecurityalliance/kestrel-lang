Besides Python package release on PyPI, Kestrel is also released into Docker
container image on DockerHub Kestrel.

The image provides a full Kestrel runtime composed of the basic Kestrel
runtime, `kestrel-jupyter`_ package, open-source Kestrel analytics in the
`kestrel-analytics repo`_, and open-source Kestrel huntbooks and tutorials in
the `kestrel-huntbook repo`_.

The image is based on the `docker-stacks`_ Jupyter image, maintained by
`Kenneth Peeples`_, and currently located under Kenneth's DockerHub account:
`kpeeples/kaas-baseline`_.

To launch the Kestrel container:

.. code-block:: console

    $ docker run kpeeples/kaas-baseline:latest


.. _kestrel-jupyter: https://github.com/opencybersecurityalliance/kestrel-jupyter
.. _kestrel-analytics repo: https://github.com/opencybersecurityalliance/kestrel-analytics
.. _kestrel-huntbook repo: https://github.com/opencybersecurityalliance/kestrel-huntbook
.. _docker-stacks: https://github.com/jupyter/docker-stacks
.. _Kenneth Peeples: https://github.com/kpeeples
.. _kpeeples/kaas-baseline: https://hub.docker.com/repository/docker/kpeeples/kaas-baseline
