from .utility import create_new_entry_type_and_csv_parser, create_named_tuple_with_name_and_fields, \
    StatementEntryToTransactionConverter


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
    matching_entry_fields_in_order=['transaction_date', ['debit_amount', 'credit_amount'],
                                    'transaction_description', 'transaction_type'],
    field_name_to_process_function={'debit_amount': lambda x: -1.0 * x}
)


LloydsCreditCardStatementEntry, LloydsCreditCardStatementParser = \
    create_new_entry_type_and_csv_parser(
        type_name='LloydsCreditCardStatementEntry',
        csv_fields=lloyds_credit_card_statement_fields
    )


LloydsCreditCardStatementEntryToTranscation = StatementEntryToTransactionConverter(
    matching_entry_fields_in_order=[
        'date', 'amount', 'description', 'reference'],
    field_name_to_process_function={'amount': lambda x: -1.0 * x}
)


StatementBundle = create_named_tuple_with_name_and_fields(
    'StatementBundle', ['parser', 'converter'])


accepted_statements = {
    'lloyds-debit': StatementBundle(LloydsAccountStatementParser, LloydsAccountsStatementEntryToTransaction),
    'lloyds-credit': StatementBundle(LloydsCreditCardStatementParser, LloydsCreditCardStatementEntryToTranscation)
}
