default: help

## Install core Kestrel package
kestrel_core:
	cd packages/kestrel_core; pip install .

## Install STIX bundle data source package
kestrel_datasource_stixbundle: kestrel_core
	cd packages/kestrel_datasource_stixbundle; pip install .

## Install STIX-Shifter data source package
kestrel_datasource_stixshifter: kestrel_core
	cd packages/kestrel_datasource_stixshifter; pip install .

## Install docker analytics
kestrel_analytics_docker: kestrel_core
	cd packages/kestrel_analytics_docker; pip install .

## Install python analytics
kestrel_analytics_python: kestrel_core
	cd packages/kestrel_analytics_python; pip install .

## Install Kestrel kernel for Jupyter
kestrel_jupyter: kestrel_datasource_stixbundle kestrel_datasource_stixshifter kestrel_analytics_docker kestrel_analytics_python
	cd packages/kestrel_jupyter; pip install .; kestrel_jupyter_setup

## Install Kestrel kernel for Jupyter
install: kestrel_jupyter

## This help screen
help:
	@printf "Available targets:\n\n"
	@awk '/^[a-zA-Z\-\_0-9%:\\]+/ { \
          helpMessage = match(lastLine, /^## (.*)/); \
          if (helpMessage) { \
            helpCommand = $$1; \
            helpMessage = substr(lastLine, RSTART + 3, RLENGTH); \
      gsub("\\\\", "", helpCommand); \
      gsub(":+$$", "", helpCommand); \
            printf "  \x1b[32;01m%-35s\x1b[0m %s\n", helpCommand, helpMessage; \
          } \
        } \
        { lastLine = $$0 }' $(MAKEFILE_LIST) | sort -u
	@printf "\n"
