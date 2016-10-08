'''
Created on 8 Oct 2016

@author: fressi
'''

import logging
import sys

from departures_web.view import Application


def main(args=None):
    # prevents to accidentally producing log messages on standard output
    out = sys.stdout
    sys.stdout = sys.stderr

    logging.basicConfig(level=logging.DEBUG)

    if not args:
        args = sys.argv

    try:
        cmd = args[1]

    except IndexError:
        cmd = 'run'

    application = Application.from_yaml()

    if cmd == 'run':
        application.run()

    elif cmd == 'get-html':
        out.write(application.get_html())
