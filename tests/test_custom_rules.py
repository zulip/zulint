"""Tests for zulint custom_rules multiline exclude_pattern support."""

import os
import tempfile
from typing import Dict, List

from zulint.custom_rules import RuleList


def _write_temp_file(content: str) -> str:
    """Write content to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".py")
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


def _make_by_lang(paths: List[str]) -> Dict[str, List[str]]:
    return {"py": paths}


class TestExcludePatternBasic:
    """Test that single-line exclude_pattern still works as before."""

    def test_exclude_pattern_suppresses_match(self) -> None:
        """An exclude_pattern matching the matched line suppresses the error."""
        content = "bad_call()\nok_call()  # noqa\ngood_call()\n"
        path = _write_temp_file(content)
        try:
            rule_list = RuleList(
                langs=["py"],
                rules=[
                    {
                        "pattern": r"_call\(\)",
                        "exclude_pattern": r"# noqa",
                        "description": "Avoid _call()",
                    },
                ],
            )
            by_lang = _make_by_lang([path])
            failed = rule_list.check(by_lang)
            # bad_call() and good_call() should fail, ok_call() should be excluded
            assert failed is True
        finally:
            os.unlink(path)

    def test_exclude_pattern_no_match(self) -> None:
        """When exclude_pattern doesn't match, all matches are reported."""
        content = "bad_call()\nanother_bad()\n"
        path = _write_temp_file(content)
        try:
            rule_list = RuleList(
                langs=["py"],
                rules=[
                    {
                        "pattern": r"bad",
                        "exclude_pattern": r"will_not_match",
                        "description": "No bad",
                    },
                ],
            )
            by_lang = _make_by_lang([path])
            failed = rule_list.check(by_lang)
            assert failed is True
        finally:
            os.unlink(path)


class TestExcludePatternContextLines:
    """Test multiline exclude_pattern with exclude_pattern_context_lines."""

    def test_context_lines_allows_next_line_exclusion(self) -> None:
        """With exclude_pattern_context_lines=1, exclude_pattern can see the next line."""
        # The pattern matches "bad_tag" on any line.
        # We want to exclude it when the NEXT line contains "# allowed".
        content = "bad_tag\n# allowed\nother_line\nbad_tag\nnot_allowed\n"
        path = _write_temp_file(content)
        try:
            rule_list = RuleList(
                langs=["py"],
                rules=[
                    {
                        "pattern": r"bad_tag",
                        "exclude_pattern": r"# allowed",
                        "exclude_pattern_context_lines": 1,
                        "description": "Avoid bad_tag",
                    },
                ],
            )
            by_lang = _make_by_lang([path])
            # First "bad_tag" (line 1) should be excluded because next line is "# allowed"
            # Second "bad_tag" (line 4) should NOT be excluded (next line is "not_allowed")
            failed = rule_list.check(by_lang)
            assert failed is True  # Second bad_tag still fails
        finally:
            os.unlink(path)

    def test_context_lines_zero_is_default_behavior(self) -> None:
        """With exclude_pattern_context_lines=0, only matched lines are checked."""
        content = "bad_tag\n# allowed\n"
        path = _write_temp_file(content)
        try:
            rule_list = RuleList(
                langs=["py"],
                rules=[
                    {
                        "pattern": r"bad_tag",
                        "exclude_pattern": r"# allowed",
                        "exclude_pattern_context_lines": 0,
                        "description": "Avoid bad_tag",
                    },
                ],
            )
            by_lang = _make_by_lang([path])
            # The exclude_pattern "# allowed" does NOT appear on the matched line,
            # so the match is NOT excluded → fails
            failed = rule_list.check(by_lang)
            assert failed is True
        finally:
            os.unlink(path)

    def test_context_lines_at_end_of_file(self) -> None:
        """exclude_pattern_context_lines handles matches at end of file gracefully."""
        content = "line1\nbad_tag\n"
        path = _write_temp_file(content)
        try:
            rule_list = RuleList(
                langs=["py"],
                rules=[
                    {
                        "pattern": r"bad_tag",
                        "exclude_pattern": r"will_not_match",
                        "exclude_pattern_context_lines": 5,
                        "description": "Avoid bad_tag",
                    },
                ],
            )
            by_lang = _make_by_lang([path])
            # Should not crash even though we request 5 extra lines at end of file
            failed = rule_list.check(by_lang)
            assert failed is True
        finally:
            os.unlink(path)

    def test_context_lines_multiple_extra(self) -> None:
        """With exclude_pattern_context_lines=2, two following lines are visible."""
        content = "bad_tag\nfirst_line\nsecond_line_ok\n"
        path = _write_temp_file(content)
        try:
            rule_list = RuleList(
                langs=["py"],
                rules=[
                    {
                        "pattern": r"bad_tag",
                        "exclude_pattern": r"second_line_ok",
                        "exclude_pattern_context_lines": 2,
                        "description": "Avoid bad_tag",
                    },
                ],
            )
            by_lang = _make_by_lang([path])
            # "second_line_ok" is 2 lines after the match, so it's in context
            failed = rule_list.check(by_lang)
            assert failed is False  # Excluded because context includes second_line_ok
        finally:
            os.unlink(path)

    def test_context_lines_not_enough(self) -> None:
        """When exclude_pattern_context_lines is too small, the exclusion doesn't trigger."""
        content = "bad_tag\nfirst_line\nsecond_line_ok\n"
        path = _write_temp_file(content)
        try:
            rule_list = RuleList(
                langs=["py"],
                rules=[
                    {
                        "pattern": r"bad_tag",
                        "exclude_pattern": r"second_line_ok",
                        "exclude_pattern_context_lines": 1,
                        "description": "Avoid bad_tag",
                    },
                ],
            )
            by_lang = _make_by_lang([path])
            # "second_line_ok" is 2 lines away but we only have 1 extra line of context
            failed = rule_list.check(by_lang)
            assert failed is True  # Not excluded
        finally:
            os.unlink(path)


class TestMultilinePatternWithMultilineExclude:
    """Test multiline pattern combined with multiline exclude."""

    def test_multiline_match_with_context_exclusion(self) -> None:
        """A multiline pattern match can be excluded based on following content."""
        # Pattern matches "?>\n" followed by any char (multiline match)
        # We exclude when the line after the match contains "<?php"
        content = "?>\nX\n<?php\nother\n?>\nY\nnot_php\n"
        path = _write_temp_file(content)
        try:
            rule_list = RuleList(
                langs=["py"],
                rules=[
                    {
                        "pattern": r"\?>\n.",
                        "exclude_pattern": r"<\?php",
                        "exclude_pattern_context_lines": 1,
                        "description": "Check closing PHP tag",
                    },
                ],
            )
            by_lang = _make_by_lang([path])
            # First match "?>\nX" → next line is "<?php" → excluded
            # Second match "?>\nY" → next line is "not_php" → NOT excluded
            failed = rule_list.check(by_lang)
            assert failed is True  # Second match still fails
        finally:
            os.unlink(path)

    def test_all_multiline_matches_excluded(self) -> None:
        """When all multiline matches are excluded, check passes."""
        content = "?>\nX\n<?php\n"
        path = _write_temp_file(content)
        try:
            rule_list = RuleList(
                langs=["py"],
                rules=[
                    {
                        "pattern": r"\?>\n.",
                        "exclude_pattern": r"<\?php",
                        "exclude_pattern_context_lines": 1,
                        "description": "Check closing PHP tag",
                    },
                ],
            )
            by_lang = _make_by_lang([path])
            failed = rule_list.check(by_lang)
            assert failed is False  # All matches excluded
        finally:
            os.unlink(path)
