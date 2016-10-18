'''
Created on 5 Oct 2016

@author: fressi
'''

import logging
import random

from flask import Flask

from transit_www.model import Model


LOG = logging.getLogger()


class Application(object):
    """Transit.org web application."""

    HTML_TEMPLATE = "html/view.html"

    SCRIPT_TEMPLATES = ["html/*.js"]

    @classmethod
    def from_yaml(cls, yaml_name='etc/departures.yml'):
        """It initializes the application using given YAML file."""

        return cls(Model.from_yaml(yaml_name))

    def __init__(self, model):
        """It creates the application instance using given model."""

        self._model = model
        self._flask_app = app = Flask(__name__)

        # add the main HTML file with embedded javascripts
        app.add_url_rule(rule='/', view_func=self.get_html, methods=['GET'])

    def run(self):
        """It runs the flask application."""

        self._flask_app.run()

    def get_html(self):
        """It produce the Web application HTML."""

        model = self._model
        scripts = []
        for script in self.SCRIPT_TEMPLATES:
            scripts.extend(model.get_text_files(script))
        gmak = random.choice(model.google_api_keys)
        return model.get_text_file(
            self.HTML_TEMPLATE, scripts='\n'.join(scripts), gmak=gmak)
