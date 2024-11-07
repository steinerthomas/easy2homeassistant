"""Utility functions for serializing objects to yaml."""

import yaml


class StringValue(str):
    """A class to represent a string value for yaml serialization."""


def quoted_str_representer(dumper, data):
    """A custom representer to quote strings in yaml."""
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')


yaml.add_representer(StringValue, quoted_str_representer)


def object_to_dict(obj):
    """Convert an object to a dictionary for yaml serialization."""
    if isinstance(obj, list):
        return [object_to_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {
            key: object_to_dict(value)
            for key, value in obj.items()
            if value is not None
        }
    if hasattr(obj, "__dict__"):
        return {
            key: object_to_dict(value)
            for key, value in obj.__dict__.items()
            if value is not None
        }
    if isinstance(obj, str):
        return StringValue(obj)
    return obj


def generic_representer(dumper, data):
    """A generic representer to convert objects to dictionaries."""
    return dumper.represent_dict(object_to_dict(data))


yaml.add_multi_representer(object, generic_representer)


def serialize_to_file(obj, file_path):
    """Serialize an object to a yaml file."""
    with open(file_path, "w", encoding="utf-8") as yaml_file:
        yaml_file.write(yaml.dump(obj, sort_keys=False, allow_unicode=True))
