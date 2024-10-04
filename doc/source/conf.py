import os
import sys
from typing import Dict, List, Optional, Tuple

import sphinx_rtd_theme  # pylint: disable=unused-import  # noqa:F401

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

sys.path.insert(0, os.path.abspath("../.."))  # noqa: PTH100

# -- Project information -----------------------------------------------------

# the master toctree document
master_doc: str = "index"

project: str = "botocraft"
copyright: str = "Caltech IMSS ADS"  # noqa: A001
author: str = "Caltech IMSS ADS"

# The full version, including alpha/beta/rc tags
release = "0.5.2"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions: List[str] = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinxcontrib.images",
    "sphinx.ext.intersphinx",
    "sphinx_rtd_theme",
    "sphinxcontrib.autodoc_pydantic",
]

source_suffix: str = ".rst"

# Add any paths that contain templates here, relative to this directory.
templates_path: List[str] = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns: List[str] = ["_build"]

add_function_parentheses: bool = False
add_module_names: bool = True

autodoc_member_order: str = "groupwise"
autodoc_type_aliases: Dict[str, str] = {}
autodoc_model_show_json: bool = False


# the locations and names of other projects that should be linked to this one
intersphinx_mapping: Dict[str, Tuple[str, Optional[str]]] = {
    "python": ("https://docs.python.org/3", None),
    "docker": ("https://docker-py.readthedocs.io/en/stable/", None),
}


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme: str = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']

html_show_sourcelink: bool = False
html_show_sphinx: bool = False
html_show_copyright: bool = True
html_theme_options = {"collapse_navigation": False}
