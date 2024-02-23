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

To have Kestrel syntax highlighting support, use the Jupyter Notebook URL
(``http://hostname:8888/nbclassic``) instead of Jupyter Lab
(``http://hostname:8888/lab``) for Kestrel huntbooks.

To find the token for the Jupyter server, you can either:

- Show it in the container log:

    .. code-block:: console

        $ docker logs <containerid>

- Go inside the container and print the token from Jupyter server:

    .. code-block:: console

        # on the host
        $ docker exec -it <containerid> /bin/bash

        # inside the container
        $ jupyter server list

.. _kestrel-jupyter: https://github.com/opencybersecurityalliance/kestrel-jupyter
.. _kestrel-analytics repo: https://github.com/opencybersecurityalliance/kestrel-analytics
.. _kestrel-huntbook repo: https://github.com/opencybersecurityalliance/kestrel-huntbook
.. _docker-stacks: https://github.com/jupyter/docker-stacks
.. _Kenneth Peeples: https://github.com/kpeeples
.. _Kenneth's DockerHub account: https://hub.docker.com/repository/docker/kpeeples/kaas-baseline
