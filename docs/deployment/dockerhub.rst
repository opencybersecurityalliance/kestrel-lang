Besides Python package (PyPI), Kestrel is also released into Docker container
image on DockerHub.

The image provides a full Kestrel runtime composed of the basic Kestrel
runtime, `kestrel-jupyter`_ package, open-source Kestrel analytics in the
`kestrel-analytics repo`_, and open-source Kestrel huntbooks and tutorials in
the `kestrel-huntbook repo`_.

The image is based on the `docker-stacks`_ Jupyter image, maintained by
`Kenneth Peeples`_, and currently located under `Kenneth's DockerHub account`_.

To launch the Kestrel container (opening Jupyter on host port 8888):

.. code-block:: console

    $ docker run -d -p 8888:8888 kpeeples/kaas-baseline:latest

To have Kestrel syntax highlighting support, use the Jupyter Notebook URL (``http://hostname:8888/tree``) instead of Jupyter Lab (``http://hostname:8888/lab``) for Kestrel huntbooks.

if the token prompt is displayed when first browsing, then get the token by going to the command prompt on the container and copying the token.  Command steps:

.. code-block:: console

    $ docker ps

.. code-block:: console

    $ docker exec -it <containerid> /bin/bash

.. code-block:: console

    $ jupyter server list

Copy the token to the token field in the brower and then you will have the folders that include the tutorials.

.. _kestrel-jupyter: https://github.com/opencybersecurityalliance/kestrel-jupyter
.. _kestrel-analytics repo: https://github.com/opencybersecurityalliance/kestrel-analytics
.. _kestrel-huntbook repo: https://github.com/opencybersecurityalliance/kestrel-huntbook
.. _docker-stacks: https://github.com/jupyter/docker-stacks
.. _Kenneth Peeples: https://github.com/kpeeples
.. _Kenneth's DockerHub account: https://hub.docker.com/repository/docker/kpeeples/kaas-baseline
