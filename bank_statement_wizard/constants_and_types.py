from .utility import create_new_entry_type_and_csv_parser, StatementEntryToTransactionConverter


lloyds_account_statement_fields = ['transaction_date', 'transaction_type', 'sort_code',
                                   'account_number', 'transaction_description', 'debit_amount',
                                   'credit_amount', 'balance']


lloyds_credit_card_statement_fields = [
    'date', 'date_entered', 'reference', 'description', 'amount']


LloydsAccountStatementEntry, LloydsAccountStatementParser = \
    create_new_entry_type_and_csv_parser(
        type_name='LloydsAccountStatementEntry',
        csv_fields=lloyds_account_statement_fields
    )


LloydsAccountsStatementEntryToTransaction = StatementEntryToTransactionConverter(
    ['transaction_date', 'debit_amount',
        'transaction_description', 'transaction_type']
)


LloydsCreditCardStatementEntry, LloydsCreditCardStatementParser = \
    create_new_entry_type_and_csv_parser(
        type_name='LloydsCreditCardStatementEntry',
        csv_fields=lloyds_credit_card_statement_fields
    )


LloydsCreditCardStatementEntryToTranscation = StatementEntryToTransactionConverter(
    ['date', 'amount', 'description', 'reference']
)
