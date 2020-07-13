import argparse
import subprocess
from typing import Sequence, Tuple

from zulint.printer import colors, print_err


def run_pycodestyle(files: Sequence[str], ignored_rules: Sequence[str]) -> bool:
    if len(files) == 0:
        return False

    failed = False
    color = next(colors)
    with subprocess.Popen(
        ['pycodestyle', '--ignore={rules}'.format(rules=','.join(ignored_rules)), '--', *files],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    ) as pep8:
        assert pep8.stdout is not None  # Implied by use of subprocess.PIPE
        for line in iter(pep8.stdout.readline, ''):
            print_err('pep8', color, line)
            failed = True
    return failed


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
        ['pyflakes', '--', *files],
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
                print_err('pyflakes', color, ln)
                failed = True
    return failed
