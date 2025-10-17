import yaml

    def load_yaml(self, yaml_file: str):
        """
        Load a YAML file and return the contents as a dictionary.
        """
        with open(self.yaml_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)