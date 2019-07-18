# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import

import re
import traceback

from zulint.printer import print_err, colors, GREEN, ENDC, MAGENTA, BLUE, YELLOW

if False:
    from typing import Dict, List, Optional, Set, Tuple
    from mypy_extensions import TypedDict

    Rule = TypedDict("Rule", {
        "bad_lines": List[str],
        "description": str,
        "exclude": Set[str],
        "exclude_line": Set[Tuple[str, str]],
        "exclude_pattern": str,
        "good_lines": List[str],
        "include_only": Set[str],
        "pattern": str,
        "strip": str,
        "strip_rule": str,
    }, total=False)
    LineTup = Tuple[int, str, str, str]


class RuleList:
    """Defines and runs custom linting rules for the specified language."""

    def __init__(self, langs, rules, max_length=None, length_exclude=[], shebang_rules=[],
                 exclude_files_in=None):
        # type: (List[str], List[Rule], Optional[int], List[str], List[Rule], Optional[str]) -> None
        self.langs = langs
        self.rules = rules
        self.max_length = max_length
        self.length_exclude = length_exclude
        self.shebang_rules = shebang_rules
        # Exclude the files in this folder from rules
        self.exclude_files_in = "\\"
        self.verbose = False

    def get_line_info_from_file(self, fn):
        # type: (str) -> List[LineTup]
        line_tups = []
        for i, line in enumerate(open(fn)):
            line_newline_stripped = line.strip('\n')
            line_fully_stripped = line_newline_stripped.strip()
            if line_fully_stripped.endswith('  # nolint'):
                continue
            tup = (i, line, line_newline_stripped, line_fully_stripped)
            line_tups.append(tup)
        return line_tups

    def get_rules_applying_to_fn(self, fn, rules):
        # type: (str, List[Rule]) -> List[Rule]
        rules_to_apply = []
        for rule in rules:
            excluded = False
            for item in rule.get('exclude', set()):
                if fn.startswith(item):
                    excluded = True
                    break
            if excluded:
                continue
            if rule.get("include_only"):
                found = False
                for item in rule.get("include_only", set()):
                    if item in fn:
                        found = True
                if not found:
                    continue
            rules_to_apply.append(rule)

        return rules_to_apply

    def check_file_for_pattern(self,
                               fn,
                               line_tups,
                               identifier,
                               color,
                               rule):
        # type: (str, List[LineTup], str, str, Rule) -> bool

        '''
        DO NOT MODIFY THIS FUNCTION WITHOUT PROFILING.

        This function gets called ~40k times, once per file per regex.

        Inside it's doing a regex check for every line in the file, so
        it's important to do things like pre-compiling regexes.

        DO NOT INLINE THIS FUNCTION.

        We need to see it show up in profiles, and the function call
        overhead will never be a bottleneck.
        '''
        exclude_lines = {
            line for
            (exclude_fn, line) in rule.get('exclude_line', set())
            if exclude_fn == fn
        }

        pattern = re.compile(rule['pattern'])
        strip_rule = rule.get('strip')  # type: Optional[str]

        ok = True
        for (i, line, line_newline_stripped, line_fully_stripped) in line_tups:
            if line_fully_stripped in exclude_lines:
                exclude_lines.remove(line_fully_stripped)
                continue
            try:
                line_to_check = line_fully_stripped
                if strip_rule is not None:
                    if strip_rule == '\n':
                        line_to_check = line_newline_stripped
                    else:
                        raise Exception("Invalid strip rule")
                if pattern.search(line_to_check):
                    if rule.get("exclude_pattern"):
                        if re.search(rule['exclude_pattern'], line_to_check):
                            continue
                    self.print_error(rule, line, identifier, color, fn, i+1)
                    ok = False
            except Exception:
                print("Exception with %s at %s line %s" % (rule['pattern'], fn, i+1))
                traceback.print_exc()

        if exclude_lines:
            print('Please remove exclusions for file %s: %s' % (fn, exclude_lines))

        return ok

    def print_error(self, rule, line, identifier, color, fn, line_number):
        # type: (Rule, str, str, str, str, int) -> None
        print_err(identifier, color, '{} {}at {} line {}:'.format(
            YELLOW + rule['description'], BLUE, fn, line_number))
        print_err(identifier, color, line)
        if self.verbose:
            if rule.get('good_lines'):
                print_err(identifier, color, GREEN + "  Good code: {}{}".format(
                    (YELLOW + " | " + GREEN).join(rule['good_lines']), ENDC))
            if rule.get('bad_lines'):
                print_err(identifier, color, MAGENTA + "  Bad code:  {}{}".format(
                    (YELLOW + " | " + MAGENTA).join(rule['bad_lines']), ENDC))
            print_err(identifier, color, "")

    def check_file_for_long_lines(self,
                                  fn,
                                  max_length,
                                  line_tups):
        # type: (str, int, List[LineTup]) -> bool
        ok = True
        for (i, line, line_newline_stripped, line_fully_stripped) in line_tups:
            if isinstance(line, bytes):
                line_length = len(line.decode("utf-8"))
            else:
                line_length = len(line)
            if (line_length > max_length and
                '# type' not in line and 'test' not in fn and 'example' not in fn and
                # Don't throw errors for markdown format URLs
                not re.search(r"^\[[ A-Za-z0-9_:,&()-]*\]: http.*", line) and
                # Don't throw errors for URLs in code comments
                not re.search(r"[#].*http.*", line) and
                not re.search(r"`\{\{ api_url \}\}[^`]+`", line) and
                    "# ignorelongline" not in line and 'migrations' not in fn):
                print("Line too long (%s) at %s line %s: %s" % (len(line), fn, i+1, line_newline_stripped))
                ok = False
        return ok

    def custom_check_file(self,
                          fn,
                          identifier,
                          color,
                          max_length=None):
        # type: (str, str, str, Optional[int]) -> bool
        failed = False

        line_tups = self.get_line_info_from_file(fn=fn)

        rules_to_apply = self.get_rules_applying_to_fn(fn=fn, rules=self.rules)

        for rule in rules_to_apply:
            ok = self.check_file_for_pattern(
                fn=fn,
                line_tups=line_tups,
                identifier=identifier,
                color=color,
                rule=rule,
            )
            if not ok:
                failed = True

        # TODO: Move the below into more of a framework.
        firstline = None
        lastLine = None
        if line_tups:
            # line_fully_stripped for the first line.
            firstline = line_tups[0][3]
            lastLine = line_tups[-1][1]

        if max_length is not None:
            ok = self.check_file_for_long_lines(
                fn=fn,
                max_length=max_length,
                line_tups=line_tups,
            )
            if not ok:
                failed = True

        if firstline:
            shebang_rules_to_apply = self.get_rules_applying_to_fn(fn=fn, rules=self.shebang_rules)
            for rule in shebang_rules_to_apply:
                if re.search(rule['pattern'], firstline):
                    self.print_error(rule, firstline, identifier, color, fn, 1)
                    failed = True

        if lastLine and ('\n' not in lastLine):
            print("No newline at the end of file. Fix with `sed -i '$a\\' %s`" % (fn,))
            failed = True

        return failed

    def check(self, by_lang, verbose=False):
        # type: (Dict[str, List[str]], bool) -> bool
        # By default, a rule applies to all files within the extension for
        # which it is specified (e.g. all .py files)
        # There are three operators we can use to manually include or exclude files from linting for a rule:
        # 'exclude': 'set([<path>, ...])' - if <path> is a filename, excludes that file.
        #                                   if <path> is a directory, excludes all files
        #                                   directly below the directory <path>.
        # 'exclude_line': 'set([(<path>, <line>), ...])' - excludes all lines matching <line>
        #                                                  in the file <path> from linting.
        # 'include_only': 'set([<path>, ...])' - includes only those files where <path> is a
        #                                        substring of the filepath.
        failed = False
        self.verbose = verbose
        for lang in self.langs:
            color = next(colors)
            for fn in by_lang[lang]:
                if fn.startswith(self.exclude_files_in) or ('custom_check.py' in fn):
                    # This is a bit of a hack, but it generally really doesn't
                    # work to check the file that defines all the things to check for.
                    #
                    # TODO: Migrate this to looking at __module__ type attributes.
                    continue
                max_length = None
                if fn not in self.length_exclude:
                    max_length = self.max_length
                if self.custom_check_file(fn, lang, color, max_length=max_length):
                    failed = True

        return failed
