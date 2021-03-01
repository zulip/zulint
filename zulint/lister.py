#!/usr/bin/env python3

import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict
from typing import Dict, List, Sequence, Union, overload

from typing_extensions import Literal


def get_ftype(fpath: str, use_shebang: bool) -> str:
    ext = os.path.splitext(fpath)[1]
    if ext:
        return ext[1:]
    elif use_shebang:
        # opening a file may throw an OSError
        with open(fpath, encoding='utf8') as f:
            first_line = f.readline()
            if re.search(r'^#!.*\bpython', first_line):
                return 'py'
            elif re.search(r'^#!.*sh', first_line):
                return 'sh'
            elif re.search(r'^#!.*\bperl', first_line):
                return 'pl'
            elif re.search(r'^#!.*\bnode', first_line):
                return 'js'
            elif re.search(r'^#!.*\bruby', first_line):
                return 'rb'
            elif re.search(r'^#!.*\btail', first_line):
                return ''  # do not lint these scripts.
            elif re.search(r'^#!', first_line):
                print('Error: Unknown shebang in file "%s":\n%s' % (fpath, first_line), file=sys.stderr)
                return ''
            else:
                return ''
    else:
        return ''

@overload
def list_files(
    group_by_ftype: Literal[False] = False,
    targets: Sequence[str] = [],
    ftypes: Sequence[str] = [],
    use_shebang: bool = True,
    modified_only: bool = False,
    exclude: Sequence[str] = [],
    extless_only: bool = False,
) -> List[str]:
    ...

@overload
def list_files(
    group_by_ftype: Literal[True],
    targets: Sequence[str] = [],
    ftypes: Sequence[str] = [],
    use_shebang: bool = True,
    modified_only: bool = False, exclude: Sequence[str] = [],
    extless_only: bool = False,
) -> Dict[str, List[str]]:
    ...

def list_files(
    group_by_ftype: bool = False,
    targets: Sequence[str] = [],
    ftypes: Sequence[str] = [],
    use_shebang: bool = True,
    modified_only: bool = False,
    exclude: Sequence[str] = [],
    extless_only: bool = False,
) -> Union[Dict[str, List[str]], List[str]]:
    """
    List files tracked by git.

    Returns a list of files which are either in targets or in directories in targets.
    If targets is [], list of all tracked files in current directory is returned.

    Other arguments:
    ftypes - List of file types on which to filter the search.
        If ftypes is [], all files are included.
    use_shebang - Determine file type of extensionless files from their shebang.
    modified_only - Only include files which have been modified.
    exclude - List of files or directories to be excluded, relative to repository root.
    group_by_ftype - If True, returns a dict of lists keyed by file type.
        If False, returns a flat list of files.
    extless_only - Only include extensionless files in output.
    """
    ftypes = [x.strip('.') for x in ftypes]
    ftypes_set = set(ftypes)

    # Really this is all bytes -- it's a file path -- but we get paths in
    # sys.argv as str, so that battle is already lost.  Settle for hoping
    # everything is UTF-8.
    repository_root = subprocess.check_output(['git', 'rev-parse',
                                               '--show-toplevel']).strip().decode('utf-8')
    exclude_abspaths = [os.path.abspath(os.path.join(repository_root, fpath)) for fpath in exclude]

    cmdline = ["git", "ls-files", "-z", *targets]
    if modified_only:
        cmdline.append('-m')

    files = [f.decode() for f in subprocess.check_output(cmdline).split(b"\0")]
    assert files.pop() == ""
    # throw away non-files (like symlinks)
    files = [f for f in files if os.path.isfile(f)]

    result_dict = defaultdict(list)  # type: Dict[str, List[str]]
    result_list = []  # type: List[str]

    for fpath in files:
        # this will take a long time if exclude is very large
        ext = os.path.splitext(fpath)[1]
        if extless_only and ext:
            continue
        absfpath = os.path.abspath(fpath)
        if any(absfpath == expath or absfpath.startswith(os.path.abspath(expath) + os.sep)
               for expath in exclude_abspaths):
            continue

        if ftypes or group_by_ftype:
            try:
                filetype = get_ftype(fpath, use_shebang)
            except (OSError, UnicodeDecodeError) as e:
                etype = e.__class__.__name__
                print('Error: %s while determining type of file "%s":' % (etype, fpath), file=sys.stderr)
                print(e, file=sys.stderr)
                filetype = ''
            if ftypes and filetype not in ftypes_set:
                continue

        if group_by_ftype:
            result_dict[filetype].append(fpath)
        else:
            result_list.append(fpath)

    if group_by_ftype:
        return result_dict
    else:
        return result_list

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List files tracked by git and optionally filter by type")
    parser.add_argument('targets', nargs='*', default=[],
                        help='''files and directories to include in the result.
                        If this is not specified, the current directory is used''')
    parser.add_argument('-m', '--modified', action='store_true', default=False,
                        help='list only modified files')
    parser.add_argument('-f', '--ftypes', nargs='+', default=[],
                        help="list of file types to filter on. "
                             "All files are included if this option is absent")
    parser.add_argument('--ext-only', dest='extonly', action='store_true', default=False,
                        help='only use extension to determine file type')
    parser.add_argument('--exclude', nargs='+', default=[],
                        help='list of files and directories to exclude from results, relative to repo root')
    parser.add_argument('--extless-only', dest='extless_only', action='store_true', default=False,
                        help='only include extensionless files in output')
    args = parser.parse_args()
    listing = list_files(targets=args.targets, ftypes=args.ftypes, use_shebang=not args.extonly,
                         modified_only=args.modified, exclude=args.exclude, extless_only=args.extless_only)
    for l in listing:
        print(l)
