"""Finds and runs all built samples to ensure that they aren't broken."""

from concurrent import futures
import argparse
import dataclasses
import logging
import pathlib
import platform
import subprocess
import stat
import sys


LOGGER = logging.getLogger(__name__)


@dataclasses.dataclass
class TestResult:
    """Information about how the test fared

    Attributes:
        returncode: The exit status of the executable when run
        executable: The path to the executable run for the test
        output_directory: The path to a directory containing files produced
          during the test. This includes logs and screenshots.
    """

    returncode: int = 0
    executable: pathlib.Path = pathlib.Path()
    output_directory: pathlib.Path = pathlib.Path()


def run_test(
    executable: pathlib.Path,
    base_output_directory: pathlib.Path,
    args: list[str] | None,
) -> TestResult:
    """Runs a test executable and returns information about what happened.

    This creates additional files in the returned TestResult output_directory:

    - stdout.txt: stdout produced when running the executable
    - stderr.txt: stderr produced when running the executable
    - returncode.txt: The exit status of running the executable
    - screenshot_frame_1.ppm: For samples that present to a window, the
      contents of the window just before exitting
    - ppx.log: The BigWheels log file
    - imgui.ini: For samples using Imgui, the Imgui configuration

    Some files might be missing if the program terminated early due to a
    failure.

    Args:
        executable: Which program to run for the text
        args: Additional arguments to provide to the executable when run

    Returns:
        A bundle of information about what happened during the test.
    """
    LOGGER.debug(f"Running: {executable}")
    output_directory = base_output_directory / f"{executable.stem}_results"
    output_directory.mkdir(parents=True, exist_ok=True)
    command = [executable, "--frame-count=2", "--screenshot-frame-number=1"]
    if args:
        command.extend(args)
    results = subprocess.run(command, capture_output=True, cwd=output_directory)
    (output_directory / "stdout.txt").write_bytes(results.stdout)
    (output_directory / "stderr.txt").write_bytes(results.stderr)
    (output_directory / "returncode.txt").write_text(str(results.returncode))
    return TestResult(
        returncode=results.returncode,
        executable=executable,
        output_directory=output_directory,
    )


def main(args: argparse.Namespace):
    """Finds all test executable and runs them.

    This function never returns. It exits with 0 if all tests passed or 1 if
    any test executable return a non-zero exit code.

    Args:
        args: Parsed arguments. See parse_args()
    """
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    test_executables = [
        file
        for file in args.build_dir.rglob(f"{args.api}_*{args.extension}")
        if file.is_file() and bool(file.stat().st_mode & stat.S_IXUSR)
    ]
    LOGGER.debug("All test executables:")
    LOGGER.debug(
        "\n".join([str(executable) for executable in test_executables]),
    )

    LOGGER.debug("Starting threadpool")
    test_succeeded = True
    with futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
        test_futures = [
            executor.submit(
                run_test,
                executable,
                args.output_dir,
                args.executable_args,
            )
            for executable in test_executables
        ]
        for completed_future in futures.as_completed(test_futures):
            result = completed_future.result()
            if result.returncode != 0:
                print(
                    f"{str(result.executable)} failed with returncode "
                    f"{str(result.returncode)}. Look at the output in "
                    f"{result.output_directory}"
                )
                test_succeeded = False

    if test_succeeded:
        print("All tests passed.")
        print(f"Results are stored in: {args.output_dir}")
        sys.exit(0)
    else:
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    repo_root = pathlib.Path(__file__).parent.parent
    build_dir = repo_root / "build"

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--build_dir",
        type=pathlib.Path,
        default=build_dir,
        help="The base of the build directory containing all test executables",
    )
    parser.add_argument(
        "--api",
        choices=("vk", "dx12"),
        default="vk",
        help="Which graphics API to test",
    )
    parser.add_argument(
        "--extension",
        choices=("", ".exe"),
        default=".exe" if platform.system() == "Windows" else "",
        help="The extension of the test executable",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print more diagnostic text",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=1,
        help="Number of test executables to run in parallel. If this is too "
        "high then tests may sporadically fail.",
    )
    parser.add_argument(
        "--output_dir",
        type=pathlib.Path,
        default=build_dir / "test_projects_results",
        help="The base of the directory to store test executable results",
    )
    parser.add_argument(
        "executable_args",
        nargs="*",
        help="Arguments passed to the test executable",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main(parse_args())
