import io
from setuptools import find_packages, setup

VERSION="1.0.0"

REQUIRED = [
    'mypy-extensions',
    'six',
    'pyflakes',
    'pycodestyle',
    'typing',
]

def long_description():
    # type: () -> str
    with io.open('README.md', encoding='utf8') as f:
        return f.read()

setup(
    name='zulint',
    version=VERSION,
    author='Zulip Open Source Project',
    description='A linter launcher for projects that have multiple source languages.',
    long_description=long_description(),
    long_description_content_type='text/markdown',
    author_email='zulip-devel@googlegroups.com',
    python_requires='>=2.7.0',
    url='https://github.com/zulip/zulint',
    packages=find_packages(exclude=('tests',)),
    package_data={
        'zulint': ["py.typed"],
    },
    install_requires=REQUIRED,
    license='Apache License 2.0',
    classifiers=[
        'Development Status :: 4 - Beta',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',

        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
)
