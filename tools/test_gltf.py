"""Renders all glTF-Sample-Assets using gltf_scene_viewer and produces a report."""

from pathlib import Path
import unittest
import json
import subprocess
import os
import shutil
import datetime
import socket

# Bigwheels checkout root
_PROJECT_ROOT = Path(__file__).parent.parent
# Build directory
_BUILD_ROOT = _PROJECT_ROOT / 'build-release'
# Place to put test results like logs and screenshots
_RESULTS_PATH = _BUILD_ROOT / 'test_gltf_results'
# Program to run to load models
# TODO Make a path that works on both Linux and Windows
_TEST_PROGRAM = _BUILD_ROOT / 'bin' / 'vk_gltf_scene_viewer'
# Where the glTF-Sample-Assets checkout is
_GLTF_SAMPLE_ASSETS = _PROJECT_ROOT / 'third_party' / 'assets' / 'glTF-Sample-Assets'
# Filename of the screenshot produced by the program under test
OUTPUT_SCREENSHOT_NAME = 'actual.ppm'
# How many frames to render before quitting
_FRAME_COUNT = 2

def _load_json(path: Path):
    """Returns a Python dict representation of the JSON in a file."""
    with path.open('r') as fd:
        return json.load(fd)


class GltfSampleAssetsTestCase(unittest.TestCase):
    """Renders all glTF-Sample-Assets and produces a report"""

    def _subtest_model(self, results_path: Path, asset_path: Path):
        """Renders a specific model using BigWheels sample app.
        
        Several files are created:

        - actual.ppm: Screenshot generated by BigWheels
        - ppx.log: Log generated by BigWheels logging framework
        - stdout.log: Standard output generate by BigWheels (looks identical to ppx.log)
        - stderr.log: Standard error generate by BigWheels
        - exit_status.txt: Exit status of the program

        Arguments:
            results_path: Place to store all the files mentioned
            asset_path: Path relative to //third_party/assets
        
        Raises:
            Some exception on failure; no exception indicates success
        """
        command = [
            str(_TEST_PROGRAM),
            '--frame-count', str(_FRAME_COUNT),
            '--screenshot-frame-number', str(_FRAME_COUNT-1),
            '--gltf-scene-file', asset_path,
            '--screenshot-path', OUTPUT_SCREENSHOT_NAME,
            '--headless']
        process = subprocess.run(command, cwd=results_path, capture_output=True)
        (results_path / 'stdout.log').write_bytes(process.stdout)
        (results_path / 'stderr.log').write_bytes(process.stderr)
        (results_path / 'exit_status.txt').write_text(str(process.returncode))
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