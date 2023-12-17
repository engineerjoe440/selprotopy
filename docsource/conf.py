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
import os
import sys
print("Build with:", sys.version)
parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0,parent_dir)
print(parent_dir)


# Verify Import
try:
    import selprotopy
except:
    print("Couldn't import `selprotopy` module!")
    sys.exit(9)


# -- Project information -----------------------------------------------------

project = 'selprotopy'
copyright = '2023, Joe Stanley'
author = 'Joe Stanley'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.autosummary',
    'numpydoc',
    #'sphinx_sitemap',
    'myst_parser',
    'sphinx_immaterial',
]
autosummary_generate = True
numpydoc_show_class_members = True


# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_immaterial'
html_title = 'selprotopy'
html_logo  = '../logo/selprotopy.png'
html_favicon = '../logo/relay.png'
html_theme_options = {

    # Specify a base_url used to generate sitemap.xml. If not
    # specified, then no sitemap will be built.
    'site_url': 'https://selprotopy.readthedocs.io/en/latest/',

    # Set the color and the accent color
    "palette": [
        {
            "primary": "light-blue",
            "accent": "blue",
            "media": "(prefers-color-scheme: light)",
            "scheme": "default",
            "toggle": {
                "icon": "material/toggle-switch-off-outline",
                "name": "Switch to dark mode",
            }
        },
        {
            "primary": "blue",
            "accent": "light-blue",
            "media": "(prefers-color-scheme: dark)",
            "scheme": "slate",
            "toggle": {
                "icon": "material/toggle-switch",
                "name": "Switch to light mode",
            }
        },
    ],

    # Set the repo location to get a badge with stats
    'repo_url': 'https://github.com/engineerjoe440/selprotopy/',
    'repo_name': 'selprotopy',

    "icon": {
        "repo": "fontawesome/brands/github",
        "logo": "material/library",
    },
}





# END