from pathlib import Path
import unittest
import json
import subprocess
import os
import shutil

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

    report = '<html><body><table>'
    report += '<thead><tr><th>Label</th><th>glTF-Sample-Assets Screenshot</th><th>BigWheels Screenshot</th><th>BigWheels Log</th></tr></thead>'
    report += '<tbody>'
    for model_spec in models_index:
        # human-readable
        label = model_spec['label']
        # path in repo
        name = model_spec['name']
        screenshot = model_spec['screenshot']
        variants = model_spec['variants']

        for variant_name in variants:
            subtest_results_name = f'{name}-{variant_name}'
            subtest_results_path = _RESULTS_PATH / subtest_results_name

            if subtest_results_path.exists():
                # TODO use knobs to give the actual PPM screenshot a better name
                # Browsers don't have great PPM support so use PNG
                subprocess.run(
                    ['convert', 'screenshot_frame_59.ppm', 'actual.png'],
                    cwd=subtest_results_path)

                # Include the glTF-Sample-Assets screenshot into the report so it is self-containted
                expected_screenshot_path = _GLTF_SAMPLE_ASSETS / 'Models' / name / screenshot
                shutil.copy2(
                    expected_screenshot_path,
                    subtest_results_path / f"expected{expected_screenshot_path.suffix}")

                report += '<tr>'
                report += f'<td>{label} ({variant_name})</td>'
                # Use relative paths so we can zip up the results folder and share
                report += f'<td><img width="640px" src="{subtest_results_name}/expected{expected_screenshot_path.suffix}"></td>'
                report += f'<td><img width="640px" src="{subtest_results_name}/actual.png"></td>'
                report += f'<td><a href="{subtest_results_name}/ppx.log">ppx.log</a></td>'
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
    # models_index = _load_json(
    #     _GLTF_SAMPLE_ASSETS / 'Models' / 'model-index.json')
    # _make_report(_RESULTS_PATH / 'report.html', models_index)
    unittest.main()