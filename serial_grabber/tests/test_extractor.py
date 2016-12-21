import unittest
from serial_grabber.extractors import TransactionExtractor


class TestExtractor(unittest.TestCase):

    def test_simple_extraction(self):
        """
        Test that the TransactionExtractor handles preceding bad data
        and only returns the actual transaction in a timely manor.
        """
        transactions = []

        def store_transaction(stream_id, transaction):
            transactions.append(transaction)

        ext = TransactionExtractor('default', 'BEGIN', 'END', store_transaction)

        self.assertEquals(0, len(transactions))

        ext.write("rubbish")

        self.assertEquals(0, len(transactions))

        ext.write("BEGIN\nSomething\n")

        self.assertEquals(0, len(transactions))

        ext.write("END\n")

        self.assertEquals(1, len(transactions))

        transaction = transactions[0].split('\n')
        self.assertEquals(3, len(transaction))
        self.assertEquals("BEGIN", transaction[0])
        self.assertEquals("Something", transaction[1])
        self.assertEquals("END", transaction[2])

    def test_multiple_transactions(self):
        transactions = []

        def store_transaction(stream_id, transaction):
            transactions.append(transaction)

        ext = TransactionExtractor('default', 'BEGIN', 'END', store_transaction)

        ext.write("""BEGIN
STEP1
END
BEGIN
STEP2
END
""")
        self.assertEquals(2, len(transactions))
        self.assertTrue('STEP1' in transactions[0])
        self.assertTrue('STEP2' in transactions[1])
