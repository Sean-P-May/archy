
import os
import yaml


def load_setup_yaml(setup_dir: str) -> dict:
    setup_path = os.path.join("setups", setup_dir, "setup.yaml")

    if not os.path.exists(setup_path):
        raise FileNotFoundError(f"Setup file not found: {setup_path}")

    with open(setup_path, "r") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")

    if not isinstance(data, dict):
        raise ValueError("Setup file must be a YAML mapping")

    return data


