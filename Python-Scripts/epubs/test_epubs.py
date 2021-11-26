from unittest import TestCase

from epubs import clean_up


class EpubTests(TestCase):
    """
    Test suite for the conversion of markdown documents, which
    have been generated from epub editions, into TEI XML.
    """

    def test_clean_up(self):
        text = ''
        result = clean_up(text)
        raise NotImplementedError()
