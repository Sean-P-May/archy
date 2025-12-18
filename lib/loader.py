
import yaml
from pathlib import Path


def load_setup_yaml(setup_dir: str, *, setups_root: str | Path = "setups") -> dict:
    setup_path = Path(setups_root) / setup_dir / "setup.yaml"

    if not setup_path.exists():
        raise FileNotFoundError(f"Setup file not found: {setup_path}")

    with open(setup_path, "r") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")

    if not isinstance(data, dict):
        raise ValueError("Setup file must be a YAML mapping")

    return data
