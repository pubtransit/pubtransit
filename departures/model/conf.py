'''
Created on 6 Oct 2016

@author: fressi
'''

import yaml

CONF = {}


def read_yaml(yaml_name):
    with open(yaml_name, "rt") as yaml_file:
        return yaml.load(yaml_file.read())


CONF.update(read_yaml('user.yml'))
