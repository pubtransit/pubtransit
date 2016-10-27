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
        app.add_url_rule(rule='/greenpin.png', view_func=self.get_greenpin,
                         methods=['GET'])
        app.add_url_rule(rule='/icon.png', view_func=self.get_icon,
                         methods=['GET'])
        for feed in self._model.iter_feeds():
            app.add_url_rule(
                rule=feed.rule, endpoint=feed.endpoint,
                view_func=feed.view_func, methods=['GET'])

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

    def get_greenpin(self):
        """It produce the Web application HTML."""
        return self._model.get_data_file('greenpin.png')

    def get_icon(self):
        """It produce the Web application HTML."""
        return self._model.get_data_file('icon.png')
