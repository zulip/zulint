import sys
from itertools import cycle

MYPY = False
if MYPY:
    from typing import Union, Text

# Terminal Color codes for use in differentiatng linters
BOLDRED = '\x1B[1;31m'
GREEN = '\x1b[32m'
YELLOW = '\x1b[33m'
BLUE = '\x1b[34m'
MAGENTA = '\x1b[35m'
CYAN = '\x1b[36m'
ENDC = '\033[0m'

colors = cycle([GREEN, YELLOW, BLUE, MAGENTA, CYAN])

def print_err(name, color, line):
    # type: (str, str, Union[Text, bytes]) -> None

    # Decode with UTF-8 if in Python 3 and `line` is of bytes type.
    # (Python 2 does this automatically)
    if sys.version_info[0] == 3 and isinstance(line, bytes):
        line = line.decode('utf-8')

    print('{color}{name}{pad}|{end} {red_color}{line!s}{end}'.format(
        color=color,
        name=name,
        pad=' ' * max(0, 10 - len(name)),
        red_color=BOLDRED,
        line=line.rstrip(),
        end=ENDC)
    )

    # Python 2's print function does not have a `flush` option.
    sys.stdout.flush()
