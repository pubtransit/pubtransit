'''
Created on 5 Oct 2016

@author: fressi
'''

import logging

from flask import Flask, request, jsonify
import six

from departures.view import get_html
from departures.model.model import Model
from departures.control.api import REST_API

import functools


LOG = logging.getLogger()


class DeparturesApplication(object):

    @classmethod
    def main(cls):
        logging.basicConfig(level=logging.DEBUG)

        model = Model.from_yaml('etc/departures.yml')
        application = cls(model)
        application.run()

    def __init__(self, model):
        self._model = model
        self._flask_app = Flask(__name__)

        # add the main HTML file with embedded javascripts
        self._add_view_function(view_function=get_html, route='/')

        # add rest API
        for control_function in REST_API:
            self._add_control_function(control_function)

    def run(self):
        self._flask_app.run()

    def _add_view_function(self, view_function, route=None):

        @functools.wraps(view_function)
        def function_wrapper():  # pylint: disable=unused-variable
            return view_function(self._model)

        self._flask_app.add_url_rule(
            route or '/view/' + view_function.__name__,
            view_func=function_wrapper, methods=['GET'])

    def _add_control_function(self, control_function):

        @functools.wraps(control_function)
        def function_wrapper():  # pylint: disable=unused-variable
            parameters = request.json
            parameters_text = ", ".join(
                "{}={}".format(k,v) for k, v in six.iteritems(parameters))
            LOG.debug(
                'process request: %s(%s)', control_function.__name__,
                parameters_text)
            return jsonify(control_function(self._model, **parameters))

        self._flask_app.add_url_rule(
            "/" + control_function.__name__,
            view_func=function_wrapper, methods=['POST'])
