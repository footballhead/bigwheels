"""Renders all glTF-Sample-Assets using gltf_scene_viewer and produces a report."""

from pathlib import Path
import unittest
import json
import subprocess
import os
import shutil
import datetime
import socket

from gltf_sample_assets_known_issues import KNOWN_ISSUES
from test_gltf import OUTPUT_SCREENSHOT_NAME

# Bigwheels checkout root
_PROJECT_ROOT = Path(__file__).parent.parent
# Build directory
_BUILD_ROOT = _PROJECT_ROOT / 'build-release'
# Place to put test results like logs and screenshots
_RESULTS_PATH = _BUILD_ROOT / 'test_gltf_results'
# Where the glTF-Sample-Assets checkout is
_GLTF_SAMPLE_ASSETS = _PROJECT_ROOT / 'third_party' / 'assets' / 'glTF-Sample-Assets'
_REPO_URL = 'https://github.com/google/bigwheels'

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
    report += '<th>Known Issues</th>'
    report += '<th>glTF-Sample-Assets Screenshot</th>'
    report += '<th>BigWheels Screenshot</th>'
    report += '<th>Exit Status</th>'
    report += '<th>Logs</th>'
    report += '</tr></thead>'
    report += '<tbody>\n'
    for model_spec in models_index:
        label = model_spec['label'] # human-readable
        name = model_spec['name'] # path in repo
        screenshot = model_spec['screenshot']
        variants = model_spec['variants']

        for variant_name in variants:
            subtest_results_name = f'{name}-{variant_name}'
            report += f'<!--{subtest_results_name}-->\n'
            subtest_results_path = _RESULTS_PATH / subtest_results_name

            if subtest_results_path.exists():
                # Browsers don't have great PPM support so use PNG.
                # Use unix command since Python doesn't have great image support.
                # TODO Replace with a solution that works on Windows
                if (subtest_results_path / OUTPUT_SCREENSHOT_NAME).exists():
                    subprocess.run(
                        ['convert', OUTPUT_SCREENSHOT_NAME, 'actual.png'],
                        cwd=subtest_results_path)

                # Include the glTF-Sample-Assets screenshot into the report so it is self-containted
                expected_screenshot_path = _GLTF_SAMPLE_ASSETS / 'Models' / name / screenshot
                shutil.copy2(
                    expected_screenshot_path,
                    subtest_results_path / f"expected{expected_screenshot_path.suffix}")

                report += '<tr>'

                # Label
                report += f'<td>{label} ({variant_name})</td>'

                # Known Issues
                report += '<td>'
                if subtest_results_name in KNOWN_ISSUES:
                    github_issues = KNOWN_ISSUES[subtest_results_name]
                    if github_issues:
                        for issue in github_issues:
                            report += f'<a href="{_REPO_URL}/issues/{issue}">#{issue}</a><br>'
                    else:
                        report += 'None'
                else:
                    report += 'Untriaged'
                report += '</td>'

                # Use relative paths so we can zip up the results folder and share

                # glTF-Sample-Assets Screenshot
                report += f'<td><img width="640px" src="{subtest_results_name}/expected{expected_screenshot_path.suffix}"></td>'

                # BigWheels Screenshot
                report += f'<td><img width="640px" src="{subtest_results_name}/actual.png"></td>'

                # Exit Status
                exit_status = (subtest_results_path / 'exit_status.txt').read_text()
                report += f'<td>{exit_status}</td>'

                # Logs
                report += f'<td><a href="{subtest_results_name}/ppx.log">ppx.log</a> - <a href="{subtest_results_name}/stdout.log">stdout.log</a> - <a href="{subtest_results_name}/stderr.log">stderr.log</a></td>'

                report += '</tr>\n'

    report += '</tbody>'
    report += '</table></body></html>'

    path.write_text(report)


def main():
    model_index = _load_json(
            _GLTF_SAMPLE_ASSETS / 'Models' / 'model-index.json')
    _make_report(_RESULTS_PATH / 'index.html', model_index)


if __name__ == '__main__':
    main()
