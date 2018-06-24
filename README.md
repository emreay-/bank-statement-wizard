# BankStatementWizard
A mini tool to parse bank statements to produce an analysis of expenses, i.e. the amount that spent on groceries/going out etc.

## Supported Statements
Currently only credit card and bank account statements from Lloyds Bank UK are supported. However, supporting another statement format is not too much of a work. Just have a look at the code starting from `constants_and_types.py`.

## What do you need?
You need to supply a simple json file in order to categorize the expenses. The json file should have the category names and a list of keywords in each category:

```
{
    "groceries": [
        "market",
        "corner shop"
    ],
    
    "eating_out": [
        "restaurant",
        "pub",
        "pizza",
        "burger"
    ],

    "regular": [
        "bill",
        "tax",
        "rent",
        "salary"
    ]
}
```

## How to use it?
Make sure that `BankStatementWizard` is in your `PYTHONPATH`. If you are not sure you can run:

```
cd path/to/BankStatementWizard/
source environment
```

Then;

```
python bank_statement_wizard -e path/to/expense_categories.json -s path/to/statement.csv -t lloyds-debit -d 01-01-2016 -o path/to/output_dir/
```

Remember to change the paths and the statement type according to your usage.

## Output
`BankStatementWizard` will parse your statement, categorize and analyze it. Then it will generate a report in pdf:

<img src="https://github.com/emreay-/BankStatementWizard/blob/master/data/sample_debit_report_p1.png" alt="drawing" width="400px"/> <img src="https://github.com/emreay-/BankStatementWizard/blob/master/data/sample_debit_report_p2.png" alt="drawing" width="400px"/>
