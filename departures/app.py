'''
Created on 5 Oct 2016

@author: fressi
'''

import logging

from flask import Flask, request, jsonify
import six

from departures.control.api import REST_API
from departures.view import get_html
import functools


LOG = logging.getLogger()


def main():
    logging.basicConfig(level=logging.DEBUG)
    app = Flask(__name__)

    # add the main HTML file with embedded javascripts
    app.add_url_rule('/', view_func=get_html, methods=['GET'])

    # add rest API
    for control_function in REST_API:
        _add_control_function(app, control_function)

    app.run()


def _add_control_function(app, control_function):

    @functools.wraps(control_function)
    def function_wrapper():  # pylint: disable=unused-variable
        parameters = request.json
        parameters_text = ", ".join(
            "{}={}".format(k,v) for k, v in six.iteritems(parameters))
        LOG.debug(
            'process request: %s(%s)', control_function.__name__,
            parameters_text)
        return jsonify(control_function(**parameters))

    app.add_url_rule(
        "/" + control_function.__name__,
        view_func=function_wrapper, methods=['POST'])

