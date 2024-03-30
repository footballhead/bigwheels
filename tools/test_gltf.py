"""Renders all glTF-Sample-Assets and produces a report."""

from pathlib import Path
import unittest
import json
import subprocess
import os
import shutil
import datetime
import socket

"""Bigwheels checkout root"""
_PROJECT_ROOT = Path(__file__).parent.parent
"""Build directory"""
_BUILD_ROOT = _PROJECT_ROOT / 'build'
"""Place to put test results like logs and screenshots"""
_RESULTS_PATH = _BUILD_ROOT / 'test_gltf_results'
# TODO Make a path that works on both Linux and Windows
"""Program to run to load models"""
_TEST_PROGRAM = _BUILD_ROOT / 'bin' / 'vk_31_gltf_basic_materials'
"""Where the glTF-Sample-Assets checkout is"""
_GLTF_SAMPLE_ASSETS = _PROJECT_ROOT / 'third_party' / 'assets' / 'glTF-Sample-Assets'
"""Filename of the screenshot produced by the program under test"""
_OUTPUT_SCREENSHOT_NAME = 'actual.ppm'
"""How many frames to render before quitting"""
_FRAME_COUNT = 2

def _load_json(path: Path):
    """Returns a Python dict representation of the JSON in a file."""
    with path.open('r') as fd:
        return json.load(fd)


def _get_git_head_commit():
    """Returns the HEAD SHA"""
    process = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True)
    return process.stdout.decode()


def _make_report(path: Path, models_index):
    """Generate an HTML summary of the test run with screenshot comparison.
    
    Arguements:
        path: Destination of the HTML report
        models_index: Loaded dict of glTF-Sample-Assets/Models/model-index.json
    """

    report = '<html><body>'
    report += f'<p>Time: {datetime.datetime.now()}</p>'
    report += f'<p>SHA: {_get_git_head_commit()}</p>'
    report += f'<p>Host: {socket.getfqdn()}</p>'
    report += '<table>'
    report += '<thead><tr>'
    report += '<th>Label</th>'
    report += '<th>glTF-Sample-Assets Screenshot</th>'
    report += '<th>BigWheels Screenshot</th>'
    report += '<th>BigWheels Log</th>'
    report += '</tr></thead>'
    report += '<tbody>'
    for model_spec in models_index:
        label = model_spec['label'] # human-readable
        name = model_spec['name'] # path in repo
        screenshot = model_spec['screenshot']
        variants = model_spec['variants']

        for variant_name in variants:
            subtest_results_name = f'{name}-{variant_name}'
            subtest_results_path = _RESULTS_PATH / subtest_results_name

            if subtest_results_path.exists():
                # Browsers don't have great PPM support so use PNG.
                # Use unix command since Python doesn't have great image support.
                # TODO Replace with a solution that works on Windows
                subprocess.run(
                    ['convert', _OUTPUT_SCREENSHOT_NAME, 'actual.png'],
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
    """Renders all glTF-Sample-Assets and produces a report"""

    def _subtest_model(self, results_path: Path, asset_path: Path):
        """Renders a specific model using BigWheels sample app.
        
        Arguments:
            results_path: Place to store logs and screenshots
            asset_path: Path relative to //third_party/assets
        
        Raises:
            Some exception on failure; no exception indicates success
        """
        # TODO: run headless to avoid taking control of the host computer
        command = [
            str(_TEST_PROGRAM),
            '--frame-count', str(_FRAME_COUNT),
            '--screenshot-frame-number', str(_FRAME_COUNT-1),
            '--gltf-scene-file', asset_path,
            '--screenshot-path', _OUTPUT_SCREENSHOT_NAME]
        process = subprocess.run(command, cwd=results_path)
        self.assertEqual(process.returncode, 0)

    def test_all(self):
        """Opens all models in //third_party/assets/glTF-Sample-Assets.
        
        Raises:
            Some exception on failure; no exception indicates success
        """
        os.mkdir(_RESULTS_PATH)

        model_index = _load_json(
            _GLTF_SAMPLE_ASSETS / 'Models' / 'model-index.json')
        for model in model_index:
            name = model['name']
            variants = model['variants']
            for variant_name in variants:
                variant_file = variants[variant_name]

                name_of_test = f'{name}-{variant_name}'
                subtest_results_path = _RESULTS_PATH / name_of_test
                bigwheels_asset_path = f'glTF-Sample-Assets/Models/{name}/{variant_name}/{variant_file}'

                os.mkdir(subtest_results_path)

                with self.subTest(name_of_test):
                    self._subtest_model(
                        subtest_results_path, bigwheels_asset_path)

        _make_report(_RESULTS_PATH / 'index.html', model_index)


if __name__ == '__main__':
    unittest.main()
