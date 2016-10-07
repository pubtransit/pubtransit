'''
Created on 6 Oct 2016

@author: fressi
'''

import jinja2
import yaml
import departures


class Model(object):

    @classmethod
    def from_yaml(cls, yaml_name):
        loader = jinja2.PackageLoader(
            package_name=departures.__name__, package_path='')
        env = jinja2.Environment(loader=loader)
        yaml_text = env.get_template(yaml_name).render()
        return cls(env=env, conf=yaml.load(yaml_text))

    def __init__(self, env, conf):
        self._env = env
        self._conf = conf
        self._text_files = {}

    @property
    def google_api_keys(self):
        return self._conf['google']['api-keys']

    def get_text_file(self, file_name, **variables):
        variables.update(self._conf)
        text_file = self._text_files.get(file_name)
        if text_file is None:
            text_file = self._env.get_template(file_name).render(**variables)
            self._text_files[file_name] = text_file
        return text_file
