'''
Created on 5 Oct 2016

@author: fressi
'''

import logging
import os

from flask import Flask, request, jsonify
import six

from departures.control import get_stops
from departures.view import get_view_file


LOG = logging.getLogger()


def main():
    logging.basicConfig(level=logging.DEBUG)
    app = Flask(__name__)

    # bind view files
    bind_view(app, "departures.html", '/')
    bind_view(app, "departures.js")

    # bind control functions
    bind_control(app, get_stops)

    app.run()


def bind_view(app, view_file_path, server_route=None):

    def _get_view_file():  # pylint: disable=unused-variable
        LOG.debug('get view file: %r', view_file_path)
        view_file = get_view_file(view_file_path)
        return view_file

    _get_view_file.__name__ = view_file_path
    app.add_url_rule(
        server_route or os.path.join('/view', view_file_path),
        view_func=_get_view_file, methods=['GET'])

def bind_control(app, control_function, server_route=None):

    def process_request():  # pylint: disable=unused-variable
        parameters = request.json
        parameters_text = ", ".join(
            "{}={}".format(k,v) for k, v in six.iteritems(parameters))
        LOG.debug(
            'process request: %s(%s)', control_function.__name__,
            parameters_text)
        return jsonify(control_function(**parameters))

    process_request.__name__ = control_function.__name__

    app.add_url_rule(
        server_route or os.path.join('/control', control_function.__name__),
        view_func=process_request, methods=['POST'])


if __name__ == "__main__":
    main()
