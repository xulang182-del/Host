import os
import yaml

config_dir = os.path.dirname(__file__)


class DictClass:
    def __init__(self):
        self._data = {}

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __contains__(self, key):
        return key in self._data

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def __str__(self):
        return str(self._data)


with open(f"{config_dir}/path.yaml", "r", encoding="utf-8") as f:
    paths = yaml.load(f, Loader=yaml.FullLoader)

project_path = paths["project_path"]
path_config = DictClass()

for key, value in paths.items():
    if r":/" not in value and r":\\" not in value:
        value = project_path + "/" + value
    setattr(path_config, key, value)
    path_config[key] = value
