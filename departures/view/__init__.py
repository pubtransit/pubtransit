'''
Created on 5 Oct 2016

@author: fressi
'''

import os

from jinja2 import Environment, PackageLoader

import departures


_ENVIRONMENT = Environment(
    loader=PackageLoader(package_name=departures.__name__, package_path=''))

_get_template = _ENVIRONMENT.get_template

_HTML_TEMPLATE = _get_template("view/view.html")

_SCRIPT_TEMPLATES = [
    _get_template("commons/logging.js"),
    _get_template("model/model.js"),
    _get_template("control/control.js"),
]


def get_html(**variables):
    # pylint: disable=no-member
    scripts = "\n".join(
        script.render(**variables) for script in _SCRIPT_TEMPLATES)
    return _HTML_TEMPLATE.render(scripts=scripts, **variables)
