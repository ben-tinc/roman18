"""
Test suite for the conversion of markdown documents, which
have been generated from epub editions, into TEI XML.
"""

from unittest import TestCase

import lxml.etree as ET

from epubs import clean_up
from epubs import split_chapters, split_titlepage
from epubs import parse_footnotes
from epubs import insert_fn_markers_xml, insert_italics_xml


class EpubCleanupTest(TestCase):
    '''Test cases for the `clean_up()` function.'''

    def test_clean_up_empty_lines(self):
        '''Empty lines should be removed.'''
        text = 'A line\n\nAnother line'
        expected = 'A line\nAnother line'
        results = clean_up(text)
        self.assertEqual(results, expected)


class EpubSplittingTest(TestCase):
    '''Test cases for functions which split texts into substrings.'''

    def test_split_titlepage(self):
        '''Titlepage should end at the second occurrence of "### ".
        
        This seems to be true at least for Wikisource documents. For documents
        from other sources, we probably need to introduce additional variants. 
        '''
        text = 'Text\n### A Heading\nText\n### First Chapter Heading\nText'
        exp_title = 'Text\n### A Heading\nText\n'
        exp_rest = '### First Chapter Heading\nText'
        title, rest = split_titlepage(text)
        self.assertEqual(exp_title, title)
        self.assertEqual(exp_rest, rest)

    def test_split_complex_titlepage(self):
        '''Ensure that additional headings on the titlepage do not confuse the processing.'''

        text = '''
## L'Ingénu
### Voltaire
##### Garnier, Paris, 1877
### CHAPITRE I.
COMMENT LE PRIEUR DE NOTRE-DAME DE LA MONTAGNE
'''
        exp_title = '\n## L\'Ingénu\n### Voltaire\n##### Garnier, Paris, 1877\n'
        exp_rest = '### CHAPITRE I.\nCOMMENT LE PRIEUR DE NOTRE-DAME DE LA MONTAGNE\n'
        title, rest = split_titlepage(text)
        self.assertEqual(exp_title, title)
        self.assertEqual(exp_rest, rest)
    
    def test_split_chapters_no_chapters(self):
        '''If there are no chapter headings, just return the whole text as a single "chapter".'''
        text = 'Text.\nMore text.'
        results = split_chapters(text)
        self.assertEqual(results, [text])

    def test_split_chapters(self):
        '''Chapters are separated by headings beginning with "### ".

        This seems to be true at least for Wikisource documents, for other sources
        we will need to introduce additional implementations.
        '''
        text = '### Ch.1\nText\n### Ch.2\nText\n### Ch.3\nText'
        results = split_chapters(text)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[1], '### Ch.2\nText\n')

    def test_split_chapters_fst_no_heading(self):
        '''Handle the case that the first segment of text has no chapter heading.'''
        text = 'Eine Art Vorwort?\n### Ch.1\nErstes Kapitel'
        results = split_chapters(text)
        self.assertEqual(results[0], 'Eine Art Vorwort?\n')
        self.assertEqual(results[1], '### Ch.1\nErstes Kapitel')


class EpubFootnoteParsing(TestCase):
    '''Test cases for extracting footnote markers.'''

    def test_parse_footnotes(self):
        '''Identify footnote marker.'''
        text = 'Text \[1\] Text.\n\n1. ↑  http://fr.wikisource.org\n'
        res_text, res_fns = parse_footnotes(text)
        exp_text = 'Text \[1\] Text.\n\n'
        exp_fns = {1: 'http://fr.wikisource.org'}
        self.assertEqual(exp_text, res_text)
        self.assertEqual(exp_fns, res_fns)
    
    def test_parse_multiple_footnotes(self):
        '''Identify multiple footnote markers.'''
        text = 'Text \[1\] text \[2\] text.\n\n1. ↑ http://fr.wikisource.org\n2. ↑  http://fr.wikisource.org\n'
        res_text, res_fns = parse_footnotes(text)
        exp_text = 'Text \[1\] text \[2\] text.\n\n'
        exp_fns = {1: 'http://fr.wikisource.org', 2: 'http://fr.wikisource.org'}
        self.assertEqual(exp_text, res_text)
        self.assertEqual(exp_fns, res_fns)

    def test_parse_footnotes_with_offset(self):
        '''Identify footnote marker and respect offset from previous chapters.
        
        We simulate that we have already found 3 footnotes in previous chapters, so
        we need to adjust our numbering accordingly.
        '''
        text = 'Text \[1\] text \[2\] text.\n\n1. ↑ http://fr.wikisource.org\n2. ↑  http://fr.wikisource.org\n'
        res_text, res_fns = parse_footnotes(text, 3)
        exp_text = 'Text \[4\] text \[5\] text.\n\n'
        exp_fns = {4: 'http://fr.wikisource.org', 5: 'http://fr.wikisource.org'}
        self.assertEqual(exp_text, res_text)
        self.assertEqual(exp_fns, res_fns)


class EpubItalicsTest(TestCase):
    '''Test cases for the XML generation of <hi> nodes.'''

    def test_insert_simple_italics(self):
        '''Test `insert_italics_xml() with unnested node.'''
        xml = '<p>Hello *from* the other side.</p>'
        root = ET.fromstring(xml)
        paragraph = insert_italics_xml(root)
        highlight = paragraph.find('hi')
        self.assertEqual(paragraph.text, 'Hello ')
        self.assertEqual(highlight.text, 'from')
        self.assertEqual(highlight.tail, ' the other side.')


    def test_insert_italics(self):
        '''Test `insert_italics_xml()`
        
        It is important that this function works not only on the text of a single
        node, but also on subnotes. Otherwise, the correctness of the output would
        depend on the order of execution.
        '''
        xml = '''
<div>
<p>Hello *from* the other side.</p>
<p>Hello <ref/> *again*.</p>
</div>
'''
        root = ET.fromstring(xml)
        div = insert_italics_xml(root)
        fst_p, snd_p = div.findall('p')
        ref = snd_p.find('ref')
        fst_hi = fst_p.find('hi')
        snd_hi = snd_p.find('hi')

        self.assertEqual(fst_p.text, 'Hello ')
        self.assertEqual(fst_hi.text, 'from')
        self.assertEqual(fst_hi.tail, ' the other side.')
        self.assertEqual(snd_p.text, 'Hello ')
        self.assertEqual(ref.text, None)
        self.assertEqual(ref.tail, ' ')
        self.assertEqual(snd_hi.text, 'again')
        self.assertEqual(snd_hi.tail, '.')


class EpubFootnotesTest(TestCase):
    '''Test cases for the XML generation of <ref> nodes.'''

    def test_insert_simple_fn_marker(self):
        '''Test `insert_fn_markers_xml()` with simple, unnested node.'''
        xml = "<p>L'Ingénu débarque en pot de chambre\[1\] dans la cour des cuisines.</p>"
        root = ET.fromstring(xml)
        paragraph = insert_fn_markers_xml(root)
        footnote = paragraph.find('ref')
        self.assertEqual(paragraph.text, "L'Ingénu débarque en pot de chambre")
        self.assertEqual(footnote.get('target'), '#N1')
        self.assertEqual(footnote.tail, " dans la cour des cuisines.")

    def test_insert_footnotes(self):
        '''Test `insert_fn_markers_xml()`
        
        It is important that this function works not only on the text of a single
        node, but also on subnotes. Otherwise, the correctness of the output would
        depend on the order of execution.
        '''