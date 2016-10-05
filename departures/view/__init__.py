'''
Created on 5 Oct 2016

@author: fressi
'''

import os

from jinja2 import Template


_VIEW_DIR = os.path.normpath(os.path.dirname(__file__))

_TEMPLATES = {}


def get_view_file(template_path, **variables):
    return _get_template(template_path).render(**variables)


def _get_template(template_path):
    full_template_path = os.path.normpath(
        os.path.join(_VIEW_DIR, template_path))
    template = _TEMPLATES.get(full_template_path)
    if template is None:
        with open(full_template_path, "rt") as template_file:
            template = Template(template_file.read())
            _TEMPLATES[full_template_path] = template
    return template
