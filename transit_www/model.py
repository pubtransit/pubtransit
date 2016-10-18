'''
Created on 6 Oct 2016

@author: fressi
'''

import glob
import json
import os

import jinja2
import yaml

import transit_www


class Model(object):
    """Data model for HTML file builder."""

    @classmethod
    def from_yaml(cls, yaml_name):
        """Load configuration form YAML file."""
        loader = jinja2.PackageLoader(
            package_name=transit_www.__name__, package_path='')
        env = jinja2.Environment(loader=loader)
        yaml_text = env.get_template(yaml_name).render()
        return cls(env=env, conf=yaml.load(yaml_text))

    def __init__(self, env, conf):
        """It creates the model given jinja environment and configuration."""
        self._env = env
        self._conf = conf
        self._text_files = {}

    @property
    def google_api_keys(self):
        """It gets Google Maps API key from configuration file."""

        return self._conf['google']['api-keys']

    def get_text_file(self, file_name, **variables):
        """It lads a template, replace veriables and return resulting file."""

        variables['transit'] = json.dumps(self._conf['transit'])
        text_file = self._text_files.get(file_name)
        if text_file is None:
            text_file = self._env.get_template(file_name).render(**variables)
            self._text_files[file_name] = text_file
        return text_file

    def get_text_files(self, file_names, **variables):
        """It lads and renders template files matching given wildcards."""

        base_dir = os.path.dirname(transit_www.__file__)
        parts = tuple(file_names.split('/'))
        full_name = os.path.join(base_dir, *parts)
        for file_name in glob.glob(full_name):
            template_name = os.path.relpath(file_name, base_dir)
            yield self.get_text_file(template_name, **variables)
