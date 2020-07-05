from setuptools import setup, find_packages

setup(
    name="bank_statement_wizard",
    version="0.1.0",
    description="A mini tool to parse bank statements to produce "
        "an analysis of expenses, i.e. the amount that spent on "
        "groceries/going out etc.",
    author="Emre Ay",
    packages=find_packages(),
    entry_points={"console_scripts": [
        "bswiz = bank_statement_wizard.__main__:main",
    ]},
    install_requires=[
        "reportlab"
    ]
)
