
# Use this YAML module as supports modifying YAML without completely changing
# file structure, preserves comments etc.
import ruamel.yaml as yaml


def load(file_path):
    """Load YAML, preserving original formatting."""
    with open(file_path) as f:
        return yaml.round_trip_load(f)


def dump(obj, file_path):
    """Dump YAML, preserving formatting and overwriting file content"""
    with open(file_path, 'w') as f:
        yaml.round_trip_dump(obj, f)
