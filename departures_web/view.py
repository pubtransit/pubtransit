'''
Created on 5 Oct 2016

@author: fressi
'''

import logging
import random

from flask import Flask

from departures_web.model import Model


LOG = logging.getLogger()


class Application(object):

    HTML_TEMPLATE = "html/view.html"

    SCRIPT_TEMPLATES = ["html/*.js"]

    @classmethod
    def from_yaml(cls, yaml_name='etc/departures.yml'):
        return cls(Model.from_yaml(yaml_name))

    def run(self):
        self._flask_app.run()

    def __init__(self, model):
        self._model = model
        self._flask_app = app = Flask(__name__)

        # add the main HTML file with embedded javascripts
        app.add_url_rule(rule='/', view_func=self.get_html, methods=['GET'])

    def get_html(self):
        model = self._model
        scripts = []
        for script in self.SCRIPT_TEMPLATES:
            scripts.extend(model.get_text_files(script))
        gmak = random.choice(model.google_api_keys)
        return model.get_text_file(
            self.HTML_TEMPLATE, scripts='\n'.join(scripts), gmak=gmak)
