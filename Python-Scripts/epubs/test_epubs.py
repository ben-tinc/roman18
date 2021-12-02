"""
Test suite for the conversion of markdown documents, which
have been generated from epub editions, into TEI XML.
"""

from unittest import TestCase

from epubs import clean_up, transform
from epubs import _wrap_paragraphs
from epubs import _wrap_headings_and_divs


class EpubCleanupTests(TestCase):
    '''Test cases for the `clean_up()` function.'''

    def test_clean_up_empty_lines(self):
        '''Empty lines should be removed.'''
        text = 'A line\n\nAnother line'
        expected = 'A line\nAnother line'
        results = clean_up(text)
        self.assertEqual(results, expected)


class EpubTransformTests(TestCase):
    '''Test cases for the XML generation.'''
    
    def test_paragraphs(self):
        '''Lines should get wrapped in p tags.'''
        text = 'A line\nAnother line'
        expected = '<p>A line</p>\n<p>Another line</p>'
        results = _wrap_paragraphs(text)
        self.assertEqual(results, expected)

    def test_paragraphs_headings(self):
        '''Lines starting with "#" are no paragraphs and should be left alone.'''
        text = '# A Heading'
        expected = '# A Heading'
        results = _wrap_paragraphs(text)
        self.assertEqual(results, expected)
