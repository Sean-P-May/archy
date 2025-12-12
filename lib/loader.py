import os
import yaml

def load_setup_yaml(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Setup file not found: {path}")

    with open(path, "r") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")

    if not isinstance(data, dict):
        raise ValueError("Setup file must be a YAML mapping")

    return data


def load_and_validate_setup(setup_dir, validator):
    setup_path = os.path.join("setups", setup_dir, "setup.yaml")
    data = load_setup_yaml(setup_path)
    validator.validate_setup(data)
    return data

