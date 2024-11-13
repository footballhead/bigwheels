"""Renders all glTF-Sample-Assets using gltf_scene_viewer and produces a report."""

from pathlib import Path
import json
import subprocess
import os
import shutil
import datetime
import socket
from typing import Optional

# Filename of the screenshot produced by the program under test
_OUTPUT_SCREENSHOT_NAME = 'actual.ppm'
_REPO_URL = 'https://github.com/google/bigwheels'

# Mapping of Label -> List of associated GitHub issues. Possible options:
# - No key? Untriaged
# - `[]`, or `None`? No known issues
# - Otherwise, a list of GitHub issue numbers (https://github.com/google/bigwheels/issues/)
KNOWN_ISSUES: dict[str, Optional[list[int]]] = {
    'ABeautifulGame-glTF': [455, 460, 461, 462],
    'AlphaBlendModeTest-glTF-Embedded': [454],
    'AlphaBlendModeTest-glTF': [453],
    'AlphaBlendModeTest-glTF-Binary': [453],
    'AnimatedCube-glTF': [457],
    'AnimatedMorphCube-glTF': [457],
    'AnimatedMorphCube-glTF-Binary': [457],
    'AnimatedMorphCube-glTF-Quantized': [455, 457],
    'AnimatedTriangle-glTF-Embedded': [452, 457],
    'AnimatedTriangle-glTF': [452, 457],
    'AnisotropyBarnLamp-glTF': [455],
    'AnisotropyBarnLamp-glTF-Binary': [455],
    'AnisotropyBarnLamp-glTF-KTX-BasisU': [455],
    'AnisotropyDiscTest-glTF': [455],
    'AnisotropyDiscTest-glTF-Binary': [455],
    'AnisotropyRotationTest-glTF': [455],
    'AnisotropyRotationTest-glTF-Binary': [455],
    'AnisotropyStrengthTest-glTF': [455, 471], # TODO: The spheres don't render properly
    'AnisotropyStrengthTest-glTF-Binary': [455, 471], # TODO: The spheres don't render properly
    'AntiqueCamera-glTF': [460],
    'AntiqueCamera-glTF-Binary': [460],
    'AttenuationTest-glTF': [455],
    'AttenuationTest-glTF-Binary': [455],
    'Avocado-glTF': [451],
    'Avocado-glTF-Binary': [451],
    'Avocado-glTF-Draco': [451, 455],
    'Avocado-glTF-Quantized': [451, 455],
    'BarramundiFish-glTF': [451],
    'BarramundiFish-glTF-Binary': [451],
    'BarramundiFish-glTF-Draco': [451, 455],
    'BoomBox-glTF': [451],
    'BoomBox-glTF-Binary': [451],
    'BoomBox-glTF-Draco': [451, 455],
    'BoomBoxWithAxes-glTF': [451],
    'Box-glTF-Embedded': None,
    'Box-glTF': None,
    'Box-glTF-Binary': None,
    'Box-glTF-Draco': [455],
    # 'Box With Spaces-glTF': [] # TODO: Triage
    'BoxAnimated-glTF-Embedded': [457],
    'BoxAnimated-glTF': [457],
    'BoxAnimated-glTF-Binary': [457],
    'BoxInterleaved-glTF-Embedded': [472],
    'BoxInterleaved-glTF': [472],
    'BoxInterleaved-glTF-Binary': [472],
    'BoxTextured-glTF-Embedded': [454],
    'BoxTextured-glTF': None,
    'BoxTextured-glTF-Binary': None,
    'BoxTexturedNonPowerOfTwo-glTF-Embedded': [454],
    'BoxTexturedNonPowerOfTwo-glTF': None,
    'BoxTexturedNonPowerOfTwo-glTF-Binary': None,
    'BoxVertexColors-glTF-Embedded': [452],
    'BoxVertexColors-glTF': [452],
    'BoxVertexColors-glTF-Binary': [452],
    'BrainStem-glTF-Embedded': [457],
    'BrainStem-glTF': [457],
    'BrainStem-glTF-Binary': [457],
    'BrainStem-glTF-Draco': [455, 457],
    'Cameras-glTF-Embedded': [452],
    'Cameras-glTF': [452],
    'CarbonFibre-glTF': [455, 460, 461],
    'CarbonFibre-glTF-Binary': [455, 460, 461],
    'CesiumMan-glTF-Embedded': [454, 457],
    'CesiumMan-glTF': [457],
    'CesiumMan-glTF-Binary': [457],
    'CesiumMan-glTF-Draco': [455, 457],
    'CesiumMilkTruck-glTF-Embedded': [451, 454],
    'CesiumMilkTruck-glTF': [451],
    'CesiumMilkTruck-glTF-Binary': [451],
    'CesiumMilkTruck-glTF-Draco': [451, 455],
    'ChairDamaskPurplegold-glTF': [455],
    'ChairDamaskPurplegold-glTF-Binary': [455],
    'ClearCoatCarPaint-glTF': [455, 460],
    'ClearCoatCarPaint-glTF-Binary': [455, 460],
    'ClearCoatTest-glTF': [451, 455, 460], # TODO: Labels don't render properly
    'ClearCoatTest-glTF-Binary': [451, 455, 460], # TODO: Labels don't render properly
    'ClearcoatWicker-glTF': [455, 460, 461],
    'ClearcoatWicker-glTF-Binary': [455, 460, 461],
    'Corset-glTF': [451],
    'Corset-glTF-Binary': [451],
    'Corset-glTF-Draco': [451, 455],
    'Cube-glTF': None,
    'DamagedHelmet-glTF-Embedded': [454, 460, 461, 462],
    'DamagedHelmet-glTF': [460, 461, 462],
    'DamagedHelmet-glTF-Binary': [460, 461, 462],
    'DiffuseTransmissionPlant-glTF': [455, 462],
    'DiffuseTransmissionPlant-glTF-Binary': [455, 462],
    'DiffuseTransmissionTeacup-glTF': [455, 460, 461],
    'DiffuseTransmissionTeacup-glTF-Binary': [455, 460, 461],
    'DirectionalLight-glTF': [455],
    'DirectionalLight-glTF-Binary': [455],
    'DispersionTest-glTF': [455],
    'DispersionTest-glTF-Binary': [455],
    'DragonAttenuation-glTF': [455],
    'DragonAttenuation-glTF-Binary': [455],
    'DragonDispersion-glTF': [455],
    'DragonDispersion-glTF-Binary': [455],
    'Duck-glTF-Embedded': [454, 473],
    'Duck-glTF': [473],
    'Duck-glTF-Binary': [473],
    'Duck-glTF-Draco': [455, 473],
    'Duck-glTF-Quantized': [455, 473],
    'EmissiveStrengthTest-glTF': [455],
    'EmissiveStrengthTest-glTF-Binary': [455],
    'EnvironmentTest-glTF': [460, 473],
    'EnvironmentTest-glTF-IBL': [460, 473],
    'FlightHelmet-glTF': None,
    'Fox-glTF': [457, 474],
    'Fox-glTF-Binary': [457, 474],
    'GlamVelvetSofa-glTF': [455, 460],
    'GlamVelvetSofa-glTF-Binary': [455, 460],
    'GlassBrokenWindow-glTF': [455],
    'GlassBrokenWindow-glTF-Binary': [455],
    'GlassHurricaneCandleHolder-glTF': [455],
    'GlassHurricaneCandleHolder-glTF-Binary': [455],
    'GlassVaseFlowers-glTF': [455],
    'GlassVaseFlowers-glTF-Binary': [455],
    'IORTestGrid-glTF': [455],
    'IORTestGrid-glTF-Binary': [455],
    'InterpolationTest-glTF': [453, 457],
    'InterpolationTest-glTF-Binary': [453, 457],
    'IridescenceAbalone-glTF': [455],
    'IridescenceAbalone-glTF-Binary': [455],
    'IridescenceDielectricSpheres-glTF': [455, 472],
    'IridescenceLamp-glTF': [455],
    'IridescenceLamp-glTF-Binary': [455],
    'IridescenceMetallicSpheres-glTF': [455, 472],
    'IridescenceSuzanne-glTF': [],
    'IridescenceSuzanne-glTF-Binary': [455],
    'IridescentDishWithOlives-glTF': [455, 473],
    'IridescentDishWithOlives-glTF-Binary': [455, 473],
    'Lantern-glTF': [451, 462],
    'Lantern-glTF-Binary': [451, 462],
    'Lantern-glTF-Draco': [451, 455, 462],
    'Lantern-glTF-Quantized': [451, 455, 462],
    'LightsPunctualLamp-glTF': [455],
    'LightsPunctualLamp-glTF-Binary': [455],
    'MandarinOrange-glTF': [473],
    'MaterialsVariantsShoe-glTF': [455],
    'MaterialsVariantsShoe-glTF-Binary': [455],
    'MeshPrimitiveModes-glTF-Embedded': [454, 475],
    'MeshPrimitiveModes-glTF': [475],
    'MetalRoughSpheres-glTF-Embedded': [454],
    'MetalRoughSpheres-glTF': [455],
    'MetalRoughSpheres-glTF-Binary': [455],
    'MetalRoughSpheresNoTextures-glTF': [452],
    'MetalRoughSpheresNoTextures-glTF-Binary': [452],
    #'MorphPrimitivesTest-glTF': [], # TODO understand morphs
    #'MorphPrimitivesTest-glTF-Binary': [],
    #'MorphPrimitivesTest-glTF-Draco': [455],
    #'MorphStressTest-glTF': [],
    #'MorphStressTest-glTF-Binary': [],
    'MosquitoInAmber-glTF': [455],
    'MosquitoInAmber-glTF-Binary': [455],
    'MultiUVTest-glTF-Embedded': [453, 454],
    'MultiUVTest-glTF': [453],
    'MultiUVTest-glTF-Binary': [453],
    'MultipleScenes-glTF-Embedded': [452],
    'MultipleScenes-glTF': [452],
    #'NegativeScaleTest-glTF': [], # TODO this renders incorrectly, understand why
    #'NegativeScaleTest-glTF-Binary': [],
    #'NormalTangentMirrorTest-glTF': [], # TODO why is left material still so shiny?; also why no back rendering?
    #'NormalTangentMirrorTest-glTF-Binary': [],
    'NormalTangentTest-glTF': [460],
    'NormalTangentTest-glTF-Binary': [460],
    'OrientationTest-glTF-Embedded': [453],
    'OrientationTest-glTF': [453],
    'OrientationTest-glTF-Binary': [453],
    'PotOfCoals-glTF': [462],
    'PotOfCoals-glTF-Binary': [262],
    'PrimitiveModeNormalsTest-glTF': [475],
    'RecursiveSkeletons-glTF': [457, 472], # TODO there's a lot wrong with this one
    'RecursiveSkeletons-glTF-Binary': [472],
    'RiggedFigure-glTF-Embedded': [457],
    'RiggedFigure-glTF': [457],
    'RiggedFigure-glTF-Binary': [457],
    'RiggedFigure-glTF-Draco': [455, 457],
    'RiggedSimple-glTF-Embedded': [454, 457], # TODO skin? rig?
    'RiggedSimple-glTF': [457],
    'RiggedSimple-glTF-Binary': [457],
    'RiggedSimple-glTF-Draco': [455, 457],
    'SciFiHelmet-glTF': None,
    'SheenChair-glTF': [455],
    'SheenChair-glTF-Binary': [455],
    'SheenCloth-glTF': [455],
    'SheenTestGrid-glTF': [455],
    'SheenTestGrid-glTF-Binary': [455],
    'SimpleInstancing-glTF': [452, 455],
    'SimpleInstancing-glTF-Binary': [452, 455],
    'SimpleMaterial-glTF-Embedded': [476],
    'SimpleMaterial-glTF': [476],
    'SimpleMeshes-glTF-Embedded': [452],
    'SimpleMeshes-glTF': [452],
    'SimpleMorph-glTF-Embedded': [452], # TODO morphs
    'SimpleMorph-glTF': [452],
    'SimpleSkin-glTF-Embedded': [452], # TODO skins
    'SimpleSkin-glTF': [452],
    'SimpleSparseAccessor-glTF-Embedded': [452], # TODO sparse accessor
    'SimpleSparseAccessor-glTF': [452],
    'SimpleTexture-glTF-Embedded': [454, 472],
    'SimpleTexture-glTF': [472],
    'SpecGlossVsMetalRough-glTF': [451, 453, 455],
    'SpecGlossVsMetalRough-glTF-Binary': [451, 453, 455],
    'SpecularSilkPouf-glTF': [455, 472],
    'SpecularSilkPouf-glTF-Binary': [455, 472],
    'SpecularTest-glTF': [455],
    'SpecularTest-glTF-Binary': [455],
    #'Sponza-glTF': [], # TODO
    'StainedGlassLamp-glTF-JPG-PNG': [455, 461, 462],
    'StainedGlassLamp-glTF': [455, 461, 462],
    'StainedGlassLamp-glTF-KTX-BasisU': [455],
    #'Suzanne-glTF': [], # TODO why so shiny????
    'TextureCoordinateTest-glTF-Embedded': [453],
    'TextureCoordinateTest-glTF': [453],
    'TextureCoordinateTest-glTF-Binary': [453],
    'TextureEncodingTest-glTF': [451, 462],
    'TextureEncodingTest-glTF-Binary': [451, 462],
    'TextureLinearInterpolationTest-glTF': [451, 462],
    'TextureLinearInterpolationTest-glTF-Binary': [451, 462],
    #'TextureSettingsTest-glTF-Embedded': [454], # TODO double-sided 
    #'TextureSettingsTest-glTF': [], # TODO
    #'TextureSettingsTest-glTF-Binary': [],
    #'TextureTransformMultiTest-glTF': [],
    #'TextureTransformMultiTest-glTF-Binary': [],
    #'TextureTransformTest-glTF': [],
    'ToyCar-glTF': [455, 473],
    'ToyCar-glTF-Binary': [455, 473],
    #'TransmissionRoughnessTest-glTF': [],
    #'TransmissionRoughnessTest-glTF-Binary': [],
    'TransmissionTest-glTF': [455, 473],
    'TransmissionTest-glTF-Binary': [455, 473],
    #'TransmissionThinwallTestGrid-glTF': [],
    #'TransmissionThinwallTestGrid-glTF-Binary': [],
    #'Triangle-glTF-Embedded': [454],
    #'Triangle-glTF': [],
    #'TriangleWithoutIndices-glTF-Embedded': [],
    #'TriangleWithoutIndices-glTF': [],
    #'TwoSidedPlane-glTF': [],
    #'Unicode❤♻Test-glTF': [],
    #'Unicode❤♻Test-glTF-Binary': [],
    #'UnlitTest-glTF': [],
    #'UnlitTest-glTF-Binary': [],
    #'VertexColorTest-glTF-Embedded': [454],
    #'VertexColorTest-glTF': [],
    #'VertexColorTest-glTF-Binary': [],
    'VirtualCity-glTF-Embedded': [454, 457, 473],
    'VirtualCity-glTF': [457, 473],
    'VirtualCity-glTF-Binary': [457, 473],
    'VirtualCity-glTF-Draco': [455, 457, 473],
    'WaterBottle-glTF': [451, 461, 462],
    'WaterBottle-glTF-Binary': [451, 461, 462],
    'WaterBottle-glTF-Draco': [451, 455, 461, 462],
    #'XmpMetadataRoundedCube-glTF': [],
    #'XmpMetadataRoundedCube-glTF-Binary': [],
}


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

    report = '<html>'
    # Alternate row color to make table easier to parse
    report += '<head><style>tbody tr:nth-child(odd) { background-color: #eee; }</style></head>'
    report += '<body>'
    report += f'<p>Time: {datetime.datetime.now()}</p>'
    commit_sha = _get_git_head_commit()
    report += f'<p>SHA: <a href="{_REPO_URL}/commit/{commit_sha}">{commit_sha}</a></p>'
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
            subtest_results_path = path.parent / subtest_results_name

            if subtest_results_path.exists():
                # Browsers don't have great PPM support so use PNG.
                # Use unix command since Python doesn't have great image support.
                # TODO Replace with a solution that works on Windows
                if (subtest_results_path / _OUTPUT_SCREENSHOT_NAME).exists():
                    subprocess.run(
                        ['convert', _OUTPUT_SCREENSHOT_NAME, 'actual.png'],
                        cwd=subtest_results_path)

                # Include the glTF-Sample-Assets screenshot into the report so it is self-containted
                expected_screenshot_path = _GLTF_SAMPLE_ASSETS / 'Models' / name / screenshot
                shutil.copy2(
                    expected_screenshot_path,
                    subtest_results_path / f"expected{expected_screenshot_path.suffix}")

                report += '<tr>'

                # Label
                report += f'<td><a href="https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/{name}/{variant_name}">{label} ({variant_name})</a></td>'

                # Known Issues
                report += '<td>'
                if subtest_results_name in KNOWN_ISSUES:
                    github_issues = KNOWN_ISSUES[subtest_results_name]
                    if github_issues:
                        for issue in github_issues:
                            report += f'<a href="{_REPO_URL}/issues/{issue}">#{issue}</a><br>'
                    else:
                        report += 'None! 🎉'
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

def _load_and_render_model(program: Path, output: Path, asset: Path):
    """Renders a specific model using BigWheels sample app.
    
    Several files are created:

    - actual.ppm: Screenshot generated by BigWheels
    - ppx.log: Log generated by BigWheels logging framework
    - stdout.log: Standard output generate by BigWheels (looks identical to ppx.log)
    - stderr.log: Standard error generate by BigWheels
    - exit_status.txt: Exit status of the program

    Arguments:
        program: TODO
        output: Place to store all the files mentioned
        asset: Path relative to //third_party/assets
    
    Raises:
        Some exception on failure; no exception indicates success
    """
    command = [
        program,
        '--frame-count', 2,
        '--screenshot-frame-number', 1,
        '--gltf-scene-asset', asset,
        '--screenshot-path', _OUTPUT_SCREENSHOT_NAME,
        '--headless']
    process = subprocess.run(command, cwd=output, capture_output=True)
    (output / 'stdout.log').write_bytes(process.stdout)
    (output / 'stderr.log').write_bytes(process.stderr)
    (output / 'exit_status.txt').write_text(str(process.returncode))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--program', type=Path)
    parser.add_argument('--model-index-json', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()

    os.mkdir(args.output)

    with args.model_index_json.open('r') as fd:
        model_index = json.load(fd)

    for model in model_index:
        name = model['name']
        variants = model['variants']
        for variant_name in variants:
            name_of_test = f'{name}-{variant_name}'
            print(name_of_test)

            subtest_results_path = args.output / name_of_test
            os.mkdir(subtest_results_path)

            variant_file = variants[variant_name]
            # TODO better way to construct this?
            bigwheels_asset_path = f'glTF-Sample-Assets/Models/{name}/{variant_name}/{variant_file}'
            _load_and_render_model(args.program, subtest_results_path, bigwheels_asset_path)

    _make_report(args.output / 'index.html', model_index)


if __name__ == '__main__':
    main()
