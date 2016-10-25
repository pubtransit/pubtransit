'''
Created on 8 Oct 2016

@author: fressi
'''

import logging
import sys

from transit_www.view import Application


def main(args=None):
    """It builds and prints to standard output the HTML page.
    """

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

    elif cmd == 'get-greenpin':
        out.write(application.get_greenpin())
