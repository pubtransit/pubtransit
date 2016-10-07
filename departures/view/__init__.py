'''
Created on 5 Oct 2016

@author: fressi
'''

import os
import random

import departures


_HTML_TEMPLATE = "view/view.html"

_SCRIPT_TEMPLATES = [
    "commons/logging.js",
    "model/model.js",
    "control/control.js",
]


def get_html(model):
    # pylint: disable=no-member
    scripts = "\n".join(
        model.get_text_file(script) for script in _SCRIPT_TEMPLATES)

    gmak = random.choice(model.google_api_keys)

    return model.get_text_file(_HTML_TEMPLATE, scripts=scripts, gmak=gmak)
