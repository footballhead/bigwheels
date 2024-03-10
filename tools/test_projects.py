"""Tests that all executables run successfully.

Test results are written to build/test_projects_results"""

import datetime
import subprocess
import sys
from pathlib import Path

"""The location of this script on the filesystem"""
_THIS_FILE_PATH = Path(__file__).absolute()
"""The directory of this script on the filesystem"""
_THIS_PATH = _THIS_FILE_PATH.parent
"""The top directory of the checkout"""
_PROJECT_ROOT = _THIS_PATH.parent

"""Root of all compiled output"""
_DEFAULT_BUILD_PATH = _PROJECT_ROOT / 'build'
# TODO windows vs Linux binpath
"""Where executable binaries are stored"""
_DEFAULT_BIN_PATH = _DEFAULT_BUILD_PATH / 'bin' / 'Debug'
"""Place to put test results"""
_DEFAULT_RESULTS_PATH = _DEFAULT_BUILD_PATH / 'test_projects_results'

"""These are not tests that we care about"""
_NOT_A_TEST = ['list_cpu_features']

# TODO what is appropriate frame count? FPS is 60 by default
_FRAME_COUNT = 60
# TODO would this be too short in CI?
_TIMEOUT_SECONDS = 30

# TODO windows vs Linux (use stat?)
# TODO upper vs lower
def is_executable(path: Path) -> bool:
    """Determines if a file is executable
    
    Arguments:
        path: The path to query
        
    Returns:
        True if executable, False otherwise
    """
    return path.suffix == '.exe'


# TODO type annotation
def list_executables(path: Path):
    """List all executables contained in a path.
    
    Arguments:
        path: A path maybe containing executables
        
    Returns:
        Generator
    """
    for child in path.iterdir():
        if is_executable(child):
            yield child


def main() -> int:
    # TODO argparse build and projects
    _DEFAULT_RESULTS_PATH.mkdir(exist_ok=True)

    failed_tests: list[Path] = []

    targets = list(list_executables(_DEFAULT_BIN_PATH))
    print(f'Found {len(targets)} tests')

    run_start_time = datetime.datetime.now()

    for i in range(len(targets)):
        print('-' * 80)
        test_start_time = datetime.datetime.now()
        bin = targets[i]
        test_name = bin.stem
        print(f'TEST {i}/{len(targets)}: {test_name}')

        if test_name in _NOT_A_TEST:
            print(f'{test_name}: SKIP (NOT A TEST)')
            continue

        test_results_path = _DEFAULT_RESULTS_PATH / test_name
        test_results_path.mkdir(exist_ok=True)

        # TODO enableDebug = true, pacedFraceRate = 0
        # TODO headless?
        command = [
            bin,
            '--frame-count', str(_FRAME_COUNT),
            '--screenshot-frame-number', str(_FRAME_COUNT - 1)]

        timed_out = False
        try:
            process = subprocess.run(
                command, capture_output=True, cwd=test_results_path,
                timeout=_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            timed_out = True

        (test_results_path / 'out.txt').write_bytes(process.stdout)
        (test_results_path / 'err.txt').write_bytes(process.stderr)

        print(f'Test time: {datetime.datetime.now() - test_start_time}')

        if timed_out:
            failed_tests.append(bin)
            print(f'{test_name}: FAIL (TIMEOUT)')
        elif process.returncode != 0:
            failed_tests.append(bin)
            print(f'{test_name}: FAIL')
        else:
            print(f'{test_name}: PASS')

    print('-' * 80)
    print(f'Total time: {datetime.datetime.now() - run_start_time}')
    if len(failed_tests) > 0:
        print('Failures:')
        for test in failed_tests:
            print(f'  {test}')
    else:
        print('All passed!')

    return 0


if __name__ == '__main__':
    sys.exit(main())
