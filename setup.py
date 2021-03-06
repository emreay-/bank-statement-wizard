from setuptools import setup, find_packages

setup(
    name="bank_statement_wizard",
    version="0.1.0",
    description="A mini tool to parse bank statements to produce "
        "an analysis of expenses, i.e. the amount that spent on "
        "groceries/going out etc.",
    author="Emre Ay",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    entry_points={"console_scripts": [
        "bswiz = bank_statement_wizard.__main__:main",
    ]},
    install_requires=[
        "matplotlib",
        "reportlab",
        "urwid",
        "urwid-utils>=0.1.2",
        "six",
        "raccoon>=3.0.0",
        "orderedattrdict"
    ]
)
