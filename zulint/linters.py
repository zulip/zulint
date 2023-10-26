import argparse
import signal
import subprocess
from typing import Callable, Sequence, Tuple

from zulint.printer import colors, print_err


def run_command(
    name: str,
    color: str,
    command: Sequence[str],
    suppress_line: Callable[[str], bool] = lambda line: False,
) -> int:
    with subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    ) as p:
        assert p.stdout is not None
        for line in iter(p.stdout.readline, ""):
            if not suppress_line(line):
                print_err(name, color, line)
        if p.wait() < 0:
            try:
                signal_name = signal.Signals(-p.returncode).name
            except (AttributeError, ValueError):
                signal_name = "signal {}".format(-p.returncode)
            print_err(
                name, color, "{} terminated by {}".format(command[0], signal_name)
            )
        return p.returncode


def run_pycodestyle(files: Sequence[str], ignored_rules: Sequence[str]) -> bool:
    if len(files) == 0:
        return False

    command = [
        "pycodestyle",
        "--ignore={rules}".format(rules=",".join(ignored_rules)),
        "--",
        *files,
    ]
    return run_command("pep8", next(colors), command) != 0


def run_pyflakes(
    files: Sequence[str],
    options: argparse.Namespace,
    suppress_patterns: Sequence[Tuple[str, str]] = [],
) -> bool:
    if len(files) == 0:
        return False
    failed = False
    color = next(colors)
    with subprocess.Popen(
        ["pyflakes", "--", *files],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    ) as pyflakes:
        # Implied by use of subprocess.PIPE
        assert pyflakes.stdout is not None
        assert pyflakes.stderr is not None

        def suppress_line(line: str) -> bool:
            for file_pattern, line_pattern in suppress_patterns:
                if file_pattern in line and line_pattern in line:
                    return True
            return False

        for ln in pyflakes.stdout.readlines() + pyflakes.stderr.readlines():
            if not suppress_line(ln):
                print_err("pyflakes", color, ln)
                failed = True
    return failed
