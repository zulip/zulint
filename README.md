# zulint

![CI](https://github.com/zulip/zulint/workflows/CI/badge.svg)

zulint is a lightweight linting framework designed for complex
applications using a mix of third-party linters and custom rules.

## Why zulint

Modern full-stack web applications generally involve code written in
several programming languages, each of which have their own standard
linter tools.  For example, [Zulip](https://zulip.com) uses Python
(mypy, Ruff), JavaScript (eslint), CSS (stylelint),
puppet (puppet-lint), shell (shellcheck), and several more.  For many
codebases, this results in linting being an unpleasantly slow
experience, resulting in even more unpleasant secondary problems like
developers merging code that doesn't pass lint, not enforcing linter
rules, and debates about whether a useful linter is "worth the time".

Zulint is the linter framework we built for Zulip to create a
reliable, lightning-fast linter experience to solve these problems.
It has the following features:

- Integrates with `git` to only checks files in source control (not
  automatically generated, untracked, or .gitignore files).
- Runs the linters in parallel, so you only have to wait for the
  slowest linter.  For Zulip, this is a ~4x performance improvement
  over running our third-party linters in series.
- Produces easy-to-read, clear terminal output, with each
  independent linter given its own color.
- Can check just modified files, or even as a `pre-commit` hook, only
  checking files that have changed (and only starting linters which
  check files that have changed).
- Handles all the annoying details of flushing stdout and managing
  color codes.
- Highly configurable.
  - Integrate a third-party linter with just a couple lines of code.
  - Every feature supports convenient include/exclude rules.
  - Add custom lint rules with a powerful regular expression
    framework.  E.g. in Zulip, we want all access to `Message` objects
    in views code to be done via our `access_message_by_id` functions
    (which do security checks to ensure the user the request is being
    done on behalf of has access to the message), and that is enforced
    in part by custom regular expression lint rules.  This system is
    optimized Python: Zulip has a few hundred custom linter rules of
    this type.
  - Easily add custom options to check subsets of your codebase,
    subsets of rules, etc.
- Has a nice automated testing framework for custom lint rules, so you
  can make sure your rules actually work.

This codebase has been in production use in Zulip for several years,
but only in 2019 was generalized for use by other projects.  Its API
to be beta and may change (with notice in the release notes) if we
discover a better API, and patches to further extend it for more use
cases are encouraged.

## Using zulint

Once a project is setup with zulint, you'll have a top-level linter
script with at least the following options:

```
$ ./example-lint --help
usage: example-lint [-h] [--modified] [--verbose-timing] [--skip SKIP]
                    [--only ONLY] [--list] [--list-groups] [--groups GROUPS]
                    [--verbose] [--fix]
                    [targets [targets ...]]

positional arguments:
  targets               Specify directories to check

optional arguments:
  -h, --help            show this help message and exit
  --modified, -m        Only check modified files
  --verbose-timing, -vt
                        Print verbose timing output
  --skip SKIP           Specify linters to skip, eg: --skip=mypy,gitlint
  --only ONLY           Specify linters to run, eg: --only=mypy,gitlint
  --list, -l            List all the registered linters
  --list-groups, -lg    List all the registered linter groups
  --groups GROUPS, -g GROUPS
                        Only run linter for languages in the group(s), e.g.:
                        --groups=backend,frontend
  --verbose, -v         Print verbose output where available
  --fix                 Automatically fix problems where supported
```


**Example Output**

```
❯ ./tools/lint
js        | Use channel module for AJAX calls at static/js/channel.js line 81:
js        |                 const jqXHR = $.ajax(args);
py        | avoid subject as a var at zerver/lib/email_mirror.py line 321:
py        |     # strips RE and FWD from the subject
py        | Please use access_message() to fetch Message objects at zerver/worker/queue_processors.py line 579:
py        |         message = Message.objects.get(id=event['message_id'])
py        | avoid subject as a var at zerver/lib/email_mirror.py line 327:
py        | Use do_change_is_admin function rather than setting UserProfile's is_realm_admin attribute directly. at file.py line 28:
py        |             user.is_realm_admin = True
puppet    | /usr/lib/ruby/vendor_ruby/puppet/util.rb:461: warning: URI.escape is obsolete
hbs       | Avoid using the `style=` attribute; we prefer styling in CSS files at static/templates/group_pms.hbs line 6:
hbs       |         <span class="user_circle_fraction" style="background:hsla(106, 74%, 44%, {{fraction_present}});"></span>
pep8      | tools/linter_lib/custom_check.py:499:13: E121 continuation line under-indented for hanging indent
pep8      | tools/linter_lib/custom_check.py:500:14: E131 continuation line unaligned for hanging indent
```

To display `good_lines` and `bad_lines` along with errors, use `--verbose` option.

```
❯ ./tools/lint --verbose
py        | Always pass update_fields when saving user_profile objects at zerver/lib/actions.py line 3160:
py        |     user_profile.save()  # Can't use update_fields because of how the foreign key works.
py        |   Good code: user_profile.save(update_fields=["pointer"])
py        |   Bad code:  user_profile.save()
py        |
py        | Missing whitespace after ":" at zerver/tests/test_push_notifications.py line 535:
py        |             'realm_counts': '[{"id":1,"property":"invites_sent::day","subgroup":null,"end_time":574300800.0,"value":5,"realm":2}]',
py        |   Good code: "foo": bar | "some:string:with:colons"
py        |   Bad code:  "foo":bar  | "foo":1
py        |
js        | avoid subject in JS code at static/js/util.js line 279:
js        |         message.topic = message.subject;
js        |   Good code: topic_name
js        |   Bad code:  subject="foo" |  MAX_SUBJECT_LEN
js        |
```

### pre-commit hook mode

See https://github.com/zulip/zulip/blob/master/tools/pre-commit for an
example pre-commit hook (Zulip's has some extra complexity because we
use Vagrant from our development environment, and want to be able to
run the hook from outside Vagrant).

## Adding zulint to a codebase

TODO: Make a pypi release

Add `zulint` to your codebase requirements file or just do:

```
pip install zulint
```

We recommend starting by copying [example-lint](./example-lint) into
your codebase and configuring it.  For a more advanced example, you
can look at [Zulip's
linter](https://github.com/zulip/zulip/blob/master/tools/lint).

```bash
cp -a example-lint /path/to/project/bin/lint
chmod +x /path/to/project/bin/lint
git add /path/to/project/bin//lint
```

## Adding third-party linters

First import the `LinterConfig` and initialize it with default arguments.
You can then use the `external_linter` method to register the linter.

eg:

```python

linter_config.external_linter('eslint', ['node', 'node_modules/.bin/eslint',
                                          '--quiet', '--cache', '--ext', '.js,.ts'], ['js', 'ts'],
                              fix_arg='--fix',
                              description="Standard JavaScript style and formatting linter"
                              "(config: .eslintrc).")
```

The `external_linter` method takes the following arguments:

* name: Name of the linter. It will be printer before the failed code to show
        which linter is failing. | `REQUIRED`
* command: The terminal command to execute your linter in "shell-like syntax".
           You can use `shlex.split("SHELL COMMAND TO RUN LINTER")` to split your
           command. | `REQUIRED`
* target_langs: The language files this linter should run on. Leave this argument
                empty (= `[]`) to run on all the files. | `RECOMMENDED`
* pass_targets: Pass target files (aka files in the specified `target_langs`) to
                the linter command when executing it. Default: `True` | `OPTIONAL`
* fix_arg: Some linters support fixing the errors automatically. Set it to the flag
           used by the linter to fix the errors. | `OPTIONAL`
* description: The description of your linter to be printed with `--list` argument. | `RECOMMENDED`

eg:

```
❯ ./tools/lint --list
Linter          Description
css             Standard CSS style and formatting linter (config: .stylelintrc)
eslint          Standard JavaScript style and formatting linter(config: .eslintrc).
puppet          Runs the puppet parser validator, checking for syntax errors.
puppet-lint     Standard puppet linter(config: tools/linter_lib/exclude.py)
templates       Custom linter checks whitespace formattingof HTML templates.
openapi         Validates our OpenAPI/Swagger API documentation(zerver/openapi/zulip.yaml)
shellcheck      Standard shell script linter.
mypy            Static type checker for Python (config: mypy.ini)
tsc             TypeScript compiler (config: tsconfig.json)
yarn-deduplicate Shares duplicate packages in yarn.lock
gitlint         Checks commit messages for common formatting errors.(config: .gitlint)
semgrep-py      Syntactic Grep (semgrep) Code Search Tool (config: ./tools/semgrep.yml)
custom_py       Runs custom checks for python files (config: tools/linter_lib/custom_check.py)
custom_nonpy    Runs custom checks for non-python files (config: tools/linter_lib/custom_check.py)
pyflakes        Standard Python bug and code smell linter (config: tools/linter_lib/pyflakes.py)
pep8_1of2       Standard Python style linter on 50% of files (config: tools/linter_lib/pep8.py)
pep8_2of2       Standard Python style linter on other 50% of files (config: tools/linter_lib/pep8.py)
```

Please make sure external linter (here `eslint`) is accessible via bash or in the
virtual env where this linter will run.

## Writing custom rules

You can write your own custom rules for any language using regular expression
in zulint. Doing it is very simple and there are tons of examples available
in [Zulip's custom_check.py file](https://github.com/zulip/zulip/blob/master/tools/linter_lib/custom_check.py).

In the [above example](#adding-third-party-linters) you can add custom rules via `@linter_config.lint` decorator.
For eg:

```python

from zulint.custom_rules import RuleList

@linter_config.lint
def check_custom_rules():
    # type: () -> int
    """Check trailing whitespace for specified files"""
    trailing_whitespace_rule = RuleList(
        langs=file_types,
        rules=[{
            'pattern': r'\s+$',
            'strip': '\n',
            'description': 'Fix trailing whitespace'
        }]
    )
    failed = trailing_whitespace_rule.check(by_lang, verbose=args.verbose)
    return 1 if failed else 0
```

#### RuleList
A new custom rule is defined via the `RuleList` class. `RuleList` takes the following arguments:

```python
langs                             # The languages this rule will run on. eg: ['py', 'bash']
rules                             # List of custom `Rule`s to run. See definition of Rule below for more details.
max_length                        # Set a max length value for each line in the files. eg: 79
length_exclude                    # List of files to exclude from `max_length` limit. eg: ["README"]
shebang_rules                     # List of shebang `Rule`s to run in `langs`. Default: []
exclude_files_in                  # Directory to exclude from all rules. eg: 'app/' Default: None
exclude_max_length_fns            # List of file names to exclude from max_length limit. eg: [test, example] Defautl: []
exclude_max_length_line_patterns  # List of line patterns to exclude from max_length limit. eg: ["`\{\{ api_url \}\}[^`]+`"]
```

#### Rule
A rule is a python dictionary containing regular expression,
which will be run on each line in the `langs`' files specified in the `RuleList`.
It has a lot of additional features which you can use to run the pattern in
specific areas of your codebase.

Find below all the keys that a `Rule` can have along with the
type of inputs they take.

```python
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
```

* `pattern` is your regular expression to be run on all the eligible lines (i.e. lines which haven't been excluded by you).
* `description` is the message that will be displayed if a pattern match is found.
* `good_lines` are the list of sample lines which shouldn't match the pattern.
* `bad_lines` are like `good_lines` but they match the pattern.

**NOTE**: `patten` is run on `bad_lines` and `good_lines` and you can use them as an example to tell the developer
      what is wrong with their code and how to fix it.

* `exclude` List of folders to exclude.
* `exclude_line` Tuple of filename and pattern to exclude from pattern check.
eg:

```python
('zerver/lib/actions.py', "user_profile.save()  # Can't use update_fields because of how the foreign key works.")`
```

* `exclude_pattern`: pattern to exclude from the matching patterns.
* `include_only`: `pattern` is only run on these files.

## Development Setup

Run the following commands in a terminal to install zulint.
```
git clone git@github.com:zulip/zulint.git
python3 -m venv zulint_env
source zulint_env/bin/activate
pip install -e .
```
