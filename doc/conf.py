# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import configparser
import pathlib
import sys

root = pathlib.Path(__file__).parent.parent
parser = configparser.ConfigParser(empty_lines_in_values=True)
parser.read(root / "setup.cfg")

try:
    import beamer2pptx
except ModuleNotFoundError:
    sys.path.append(str(root.joinpath("src").resolve()))
    import beamer2pptx

# -- Project information -----------------------------------------------------

project = parser.get("build_sphinx", "project")
author = parser.get("metadata", "author")
copyright = "2021, " + author
release = parser.get("metadata", "version")
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.githubpages",
    "sphinx.ext.napoleon",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "kpruss"

html_theme_options = {
    "avatar": "https://avatars.githubusercontent.com/kprussing",
    "github": "kprussing",
    "email": "kprussing74@gmail.com",
    "linkedin": "kprussing",
    "stackoverflow": "4249913",
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
