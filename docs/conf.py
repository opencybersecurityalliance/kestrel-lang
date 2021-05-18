project = "Kestrel Threat Hunting Language"
release = "1.0.0"
author = "Xiaokui Shu, Paul Coccoli"
copyright = "2021 IBM"

extensions = [
    "sphinx.ext.intersphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    # "undoc-members": True,
    "show-inheritance": True
}

html_title = project
html_theme = "sphinx_rtd_theme"
highlight_language = "none"
