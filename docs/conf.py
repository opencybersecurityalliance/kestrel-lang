import os
from configparser import RawConfigParser

def get_version():
    """Return package version from setup.cfg."""
    config = RawConfigParser()
    config.read(os.path.join("..", "setup.cfg"))
    return config.get("metadata", "version")

project = "Kestrel Threat Hunting Language"
version = get_version()
release = version
author = "Xiaokui Shu, Paul Coccoli"
copyright = "2022 Open Cybersecurity Alliance"

extensions = [
    "sphinx.ext.intersphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosectionlabel",
]

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    # "undoc-members": True,
    "show-inheritance": True
}

suppress_warnings = ['autosectionlabel.*']

autosectionlabel_prefix_document = True

html_title = project
html_theme = "sphinx_rtd_theme"
highlight_language = "none"
