import yaml


def load_yaml(yaml_file: str) -> dict:
    """
    Load a YAML file and return the contents as a dictionary.
    """
    with open(yaml_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
