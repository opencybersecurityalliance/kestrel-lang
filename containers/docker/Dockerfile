# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
# for reference on tutorials and data see https://github.com/opencybersecurityalliance/kestrel-huntbook/tree/main/.binder
# This is the WG copy.  kestrel-lang contains master - source of truth
ARG OWNER=jupyter
ARG BASE_CONTAINER=$OWNER/base-notebook
FROM $BASE_CONTAINER

LABEL maintainer="Jupyter Project <jupyter@googlegroups.com>"

# Fix: https://github.com/hadolint/hadolint/wiki/DL4006
# Fix: https://github.com/koalaman/shellcheck/wiki/SC3014
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# ROOT ACTIVITIES
USER root
# Install all OS dependencies for fully functional notebook server
RUN apt-get update --yes && \
    apt-get install --yes --no-install-recommends \
    # Common useful utilities
    git \
    curl \
    gnupg\
    nano-tiny \
    tzdata \
    unzip \
    vim-tiny \
    openssh-client \
    less \
    texlive-xetex \
    texlive-fonts-recommended \
    texlive-plain-generic \
    xclip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# install prerequisites
# 1. from requirements.txt for jupyter hub
# https://github.com/opencybersecurityalliance/kestrel-huntbook/blob/main/.binder/requirements.txt
# analytics::dataexfiltration analytics::log4shell analytics::piniponmap analytics::sklearn-cluster analytics::attribute-plot analytics::suspiciousscoring 
#RUN pip install flask flask-cors tabulate urllib3 geoip2 folium scikit-learn gower business-rules matplotlib
#leaving this off until confirmation required for docker vs binder
# 2. from apt.txt
# analytics prereq for cloning data-bucket-kestrel
# mapped to apt.txt https://github.com/opencybersecurityalliance/kestrel-huntbook/blob/main/.binder/apt.txt
# debian required
# from postbuild
# https://github.com/opencybersecurityalliance/kestrel-huntbook/blob/main/.binder/postBuild
################################
# 1. Setup Git LFS - to setup gitlab-lfs for this container it has to be grabbed from the site as git-lfs is not in the repo for the base
################################
# analytics prereq
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash
RUN sudo apt-get install --yes git-lfs
RUN mkdir -p /opt/kaas && chown ${NB_UID}:${NB_UID} /opt/kaas
COPY kaas-logo-san-seriff.png /opt/kaas/kaas-logo-san-seriff.png

# USER ACTIVITIES
# Switch back to jovyan to avoid accidental container runs as root
USER ${NB_UID}
RUN git lfs install
################################
# 2. Setup Kestrel Kernel
################################
RUN kestrel_jupyter_setup
################################
RUN mv "${HOME}/.local/share/jupyter/kernels/kestrel"* "${CONDA_DIR}/share/jupyter/kernels/" && \
    chmod -R go+rx "${CONDA_DIR}/share/jupyter" && \
    rm -rf "${HOME}/.local"
# Add R mimetype option to specify how the plot returns from R to the browser
RUN curl https://raw.githubusercontent.com/kpeeples/kestrel-as-a-service/main/dockerhub/Rprofile.site -o ${HOME}/Rprofile.site
RUN chown ${NB_UID}:${NB_GID} ${HOME}/Rprofile.site && mkdir -p /opt/conda/lib/R/etc && mv Rprofile.site /opt/conda/lib/R/etc/Rprofile.site
# from postbuild
# https://github.com/opencybersecurityalliance/kestrel-huntbook/blob/main/.binder/postBuild
################################
# 3. Obtain Data -- This copies all data and notebooks required
# Place data in /opt/kaas and then move to home for 
# KaaS (Kubernetes/Jupyterhub/Containers)
################################
RUN git clone https://github.com/opencybersecurityalliance/data-bucket-kestrel.git /opt/kaas/data-bucket-kestrel
RUN git clone https://github.com/opencybersecurityalliance/kestrel-huntbook.git /opt/kaas/kestrel-huntbook
RUN git clone https://github.com/opencybersecurityalliance/kestrel-analytics.git /opt/kaas/kestrel-analytics

# from postbuild
# https://github.com/opencybersecurityalliance/kestrel-huntbook/blob/main/.binder/postBuild
################################
# 4. Setup Configurations
################################
RUN mkdir -p /home/jovyan/.config/kestrel && \
    mv /opt/kaas/kestrel-huntbook/config/stixshifter.yaml /home/jovyan/.config/kestrel/ && \
    ln -s /home/jovyan/.config/kestrel/stixshifter.yaml /opt/kaas/kestrel-huntbook/huntbooks/stixshifter.yaml && \
    ln -s /home/jovyan/.config/kestrel/stixshifter.yaml /opt/kaas/kestrel-huntbook/tutorial/stixshifter.yaml && \
    ln -s /home/jovyan/.config/kestrel/stixshifter.yaml /opt/kaas/kestrel-huntbook/blackhat22/stixshifter.yaml
# this enables trusted ipynb files for jupyter
RUN jupyter trust */*.ipynb

