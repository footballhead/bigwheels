import json
from pathlib import Path

# Bigwheels checkout root
_PROJECT_ROOT = Path(__file__).parent.parent
# Where the glTF-Sample-Assets checkout is
_GLTF_SAMPLE_ASSETS = _PROJECT_ROOT / 'third_party' / 'assets' / 'glTF-Sample-Assets'


def _load_json(path: Path):
    """Returns a Python dict representation of the JSON in a file."""
    with path.open('r') as fd:
        return json.load(fd)


def main():
    model_index = _load_json(
            _GLTF_SAMPLE_ASSETS / 'Models' / 'model-index.json')
    print('KNOWN_ISSUES: dict[str, Optional[list[int]]] = {')
    for model_spec in model_index:
        name = model_spec['name'] # path in repo
        variants = model_spec['variants']
        for variant_name in variants:
            subtest_results_name = f'{name}-{variant_name}'
            print(f"    '{subtest_results_name}': [],")
    print('}')


if __name__ == '__main__':
    main()
