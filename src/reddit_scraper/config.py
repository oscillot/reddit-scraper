import os
import json

HERE = os.path.dirname(__file__)


def get_config():
    return Config(os.path.join(HERE, 'config.json'))


class Config(object):
    """
    The config class is the entry point to the Configurable Object class.

    :param str or dict or list json_fp: a str representing the path to the json
    config file on disk. This value gets passed to the :class: Configurable
    class
    :param bool force_string: whether to try to return an object where the
    values are byte string objects instead of unicode objects. Useful for
    interfaces that will use the data in string buffers or similar.
    """
    def __init__(self, json_fp, force_string=False):
        if type(json_fp) == str:
            f_json = open(json_fp, 'r')
            try:
                json_conf = json.loads(f_json.read())
            except ValueError:
                raise ValueError('No JSON object could be decoded: This usually '
                                 'means there is an error in the JSON data. Check'
                                 ' the file at %s for JSON format compatibility.'
                                 % json_fp)
            f_json.close()
        elif type(json_fp) == dict:
            json_conf = json_fp
        else:
            raise ValueError('Not JSON Fool: %s' % type(json_fp))
        self.data = json_conf
        self.force_string = force_string
        if force_string:
            self.data = self.convert(self.data)

    def __getitem__(self, item):
        return self.data[item]

    def update(self, data):
        self.data.update(data)

    def get(self, item, default=None):
        return self.data.get(item, default)

    def convert(self, data):
        """
        recursively converts a dictionary retrieved from a json so that any
        values that are unicode are now strings. this is useful when the
        values are used as buffers.
        """
        if isinstance(data, dict):
            #worth mentioning that this dictionary builder doesn't work in
            # python 2.6
            return {self.convert(key): self.convert(value) for key,
                                       value in data.iteritems()}
        elif isinstance(data, list):
            return [self.convert(element) for element in data]
        elif isinstance(data, unicode):
            return data.encode('utf-8')
        else:
            return data