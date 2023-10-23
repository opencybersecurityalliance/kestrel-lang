import tomllib

def get_version():
    """Use the kestrel_jupyter (umbralla package) version as doc version"""
    with open("../packages/kestrel_jupyter/pyproject.toml", "rb") as f:
        pyproject_config = tomllib.load(f)
    return pyproject_config["project"]["version"]

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
    "sphinx_design",
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
html_logo = "../logo/logo_w_text_white.png"
html_theme_options = {
    'logo_only': True,
    'display_version': False,
}
html_static_path = ['_static']
html_css_files = [
    'css/logo.css',
    'css/table.css',
]
