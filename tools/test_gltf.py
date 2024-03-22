from pathlib import Path
import unittest
import json
import subprocess
import os

"""Bigwheels checkout root"""
_PROJECT_ROOT = Path(__file__).parent.parent
"""Build directory"""
_BUILD_ROOT = _PROJECT_ROOT / 'build'
"""Place to put test results like logs and screenshots"""
_RESULTS_PATH = _BUILD_ROOT / 'test_gltf_results'
"""Program to run to load models"""
_TEST_PROGRAM = _BUILD_ROOT / 'bin' / 'vk_31_gltf_basic_materials'
"""Where the glTF-Sample-Assets checkout is"""
_GLTF_SAMPLE_ASSETS = _PROJECT_ROOT / 'third_party' / 'assets' / 'glTF-Sample-Assets'


def _load_json(path: Path):
    """Returns a Python dict representation of the JSON in a file."""
    with path.open('r') as fd:
        return json.load(fd)


def _make_report(path: Path, models_index):
    """Generate an HTML summary of the test run with screenshot comparison"""

    # TODO: Consider turning PGM to PNG here instead of during the test

    report = '<html><body><table>'
    report += '<thead><tr><th>Label</th><th>glTF-Sample-Assets Screenshot</th><th>BigWheels Screenshot</th></tr></thead>'
    report += '<tbody>'
    for model_spec in models_index:
        # human-readable
        label = model_spec['label']
        # path in repo
        name = model_spec['name']
        screenshot = model_spec['screenshot']
        variants = model_spec['variants']

        for variant_name in variants:
            variant_file = variants[variant_name]
            report += '<tr>'
            report += f'<td>{label} ({variant_name})</td>'
            report += f'<td><img src="{str(_GLTF_SAMPLE_ASSETS)}/Models/{name}/{screenshot}"></td>'
            report += f'<td><img src="{str(_RESULTS_PATH)}/{name}-{variant_name}/screenshot_frame_59.png"></td>'
            report += '</tr>'

    report += '</tbody>'
    report += '</table></body></html>'

    path.write_text(report)



class GltfSampleAssetsTestCase(unittest.TestCase):
    def _subtest_model(self, model_spec):
        """Open all variants of a model
        
        Arguments:
            model_spec: Model object in model-index.json
        
        Raises:
            Some exception on failure; none is success
        """
        name = model_spec['name']
        variants = model_spec['variants']
        for variant_name in variants:
            variant_file = variants[variant_name]

            subtest_results_path = _RESULTS_PATH / f'{name}-{variant_name}'
            os.mkdir(subtest_results_path)

            bigwheels_asset_path = f'glTF-Sample-Assets/Models/{name}/{variant_name}/{variant_file}'
            command = [
                str(_TEST_PROGRAM),
                '--frame-count', '60',
                '--screenshot-frame-number', '59',
                '--gltf-scene-file', bigwheels_asset_path]
            process = subprocess.run(command, cwd=subtest_results_path)

            self.assertEqual(process.returncode, 0)

            # Make a PNG for the report (consider doing this outside the test)
            subprocess.run(
                ['convert', 'screenshot_frame_59.ppm', 'screenshot_frame_59.png'],
                cwd=subtest_results_path)

    def test_all(self):
        """Opens all models in glTF-Sample-Assets.
        
        Raises:
            Some exception on failure; none is success
        """
        os.mkdir(_RESULTS_PATH)

        models_index = _load_json(
            _GLTF_SAMPLE_ASSETS / 'Models' / 'model-index.json')
        for model_spec in models_index:
            with self.subTest(model_spec):
                self._subtest_model(model_spec)
        
        _make_report(_RESULTS_PATH / 'report.html', models_index)


if __name__ == '__main__':
    unittest.main()
