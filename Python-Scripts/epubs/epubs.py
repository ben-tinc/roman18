'''This Script generates an xml-file from txt-data.'''

import xml.etree.ElementTree as ET
import os.path
import glob
import logging
from pathlib import Path
import re

#set a path where your data are saved
SOURCE_PATH = "sources/"
#set a path where you want to save your data
SAVE_PATH = 'results/'


def prepare(save_path):
    '''Ensure that the configured `SAVE_PATH` exists.'''
    p = Path(save_path)
    p.mkdir(parents=True, exist_ok=True)
    
    if any(p.iterdir()):
        msg = f'SAVE_PATH "{p.absolute()}" is not empty, we might override previous results.'
        logging.warning(msg)
    
    return p


def open_file(path):
    with open(path, encoding='utf-8') as f:
        text = f.read()
    return text


def clean_up(text):
    '''Delete and/or replace unnecessary text artifacts.'''
    text = (
        text.replace('&', '&amp;')
            .replace('\!', '')
            .replace('\*', '*')
            .replace('* * *', '')
            .replace('\(', '(')
            .replace('\)', ')')
    )
    # Delete empty lines.
    text = '\n'.join([line for line in text.split('\n') if line.strip()])
    return text


def split_titlepage(text):
    '''Split on the second occurence of "### ".'''
    # How to recognize the end of the titlepage
    marker = '\n### '
    end_of_titlepage = text.find(marker, text.find(marker)+len(marker))
    # Add 1 to index so that the newline still belongs to the titlepage.
    titlepage, rest = text[:end_of_titlepage+1], text[end_of_titlepage+1:]
    return titlepage, rest


def split_chapters(text):
    '''Split on occurrences of "### ". This is relevant because footnotes are
    numbered by chapter.
    '''
    pass


def build_titlepage_xml(text):
    '''Wrap the elements of the titlepage in appropriate XML elements.'''
    front = ET.Element('front')
    titlepage = ET.Element('div', attrib={'type': 'titlepage'})
    
    # Wrap lines in either head or paragraph tags.
    for line in text.split('\n'):
        line = line.strip()
        if line and line.startswith('#'):
            h = ET.Element('head')
            h.text = line.replace('#', '').strip()
            titlepage.append(h)
        elif line:
            p = ET.Element('p')
            p.text = line.strip()
            titlepage.append(p)
    front.append(titlepage)
    return front


def build_body_xml(text):
    '''Wrap elements of the text body in appropriate XML elements.'''
    body = ET.Element('body')
    
    # If we are currently inside a div, keep track of it.
    div = None
    # Collect all the footnotes along the way.
    notes = {}

    for line in text.split('\n'):
        if line.startswith('#'):
            # Start a new div and place a head element inside.
            div = ET.Element('div', attrib={'type': 'chapter'})
            head = ET.SubElement(div, 'head')
            head.text = line.replace('#', '').strip()
            body.append(div)
        elif re.match('\d+\. ↑', line):

        elif line:
            # Create a new paragraph either inside an existing div or directly in body.
            parent = div if div is not None else body
            p = ET.Element('p')
            p.text = line.strip()

            p = parse_italics(p)
            
            parent.append(p)
    
    return body


def parse_footnotes(body):
    pattern = r''
    notes = {}

    for node in body.iter():


    return body, notes



def parse_italics(paragraph):
    '''Create a paragraph with markup for italics if applicable.'''
    # Non-greedy pattern (i.e. match as little as possible) for italic text segments.
    italic = r'(\*.*?\*)'
    segments = re.split(italic, paragraph.text)

    # Check if there are actually italic segments.
    if len(segments) > 1:
        # Process italics:
        last_node = paragraph
        i = 0
        while i < len(segments):
            seg = segments[i]
            # Case 1: non-italic at the start of the paragraph. This should be
            #         in the `text` part of the paragraph.
            if not seg.startswith('*') and i == 0:
                paragraph.text = seg
            # Case 2: non-italic somewhere in the middle of the paragraph. This is
            #         supposed to be the `tail` of a previously created <hi> node.
            elif not seg.startswith('*'):
                last_node.tail = seg
            # Case 3: italic text. Create a new <hi> node and set its text content.
            #         Then append it to the paragraph.
            elif seg.startswith('*'):
                content = seg.strip('*')
                new_node = ET.Element('hi', attrib={'rend': 'italic'})
                new_node.text = content
                last_node = new_node
                paragraph.append(new_node)
            i += 1
    
    return paragraph


def transform(text):
    """Create an XML tree with data extracted from the text."""
    titlepage, rest = split_titlepage(text)

    # Create root node.
    text_node = ET.Element('text')
    xml = ET.ElementTree(text_node)

    # Create front segment.
    front = build_titlepage_xml(titlepage)
    text_node.append(front)

    # Create text body segment.
    body = build_body_xml(rest)
    text_node.append(body)

    return xml


def write_results(xml, save_path, file_name):
    """Write results to configured `SAVE_PATH`."""
    name = file_name.replace('.txt', '.xml')
    p = Path(save_path) / name
    p = str(p.absolute())
    
    logging.debug(f'writing results to {p}.')
    
    # Pretty-print the xml.
    ET.indent(xml)
    xml.write(p, encoding='utf-8')


def edition(path, save_path):
    for file in glob.glob(path):
        # open and read file
        f = open(file, "r", encoding="utf8")
        r = f.read()
        #generate xml-tree
        r = '<text>\n<front>\n<div  type="titlepage">'+r+'</div>\n</body>\n</text>'
        #delete and replace unnecessary data
        r = r.replace("&", "&amp;")
        r = r.replace('\!', '')
        r = r.replace('\*','*')
        r = r.replace('* * *', '')
        r = r.replace('\(','(')
        r = r.replace('\)',')')
        #delete empty lines
        r = [line for line in r.split('\n') if line.strip() != '']
        r = '\n'.join(r)
        #set paragraph tags at line-breaks
        r = r.replace('\n','</p>\n<p>')
        r = r.replace('<text></p>', '<text>')
        r = r.replace('<p><front></p>', '<front>')
        r = r.replace('<p><div','<div')
        r = r.replace('<p></div></p>\n<p></body></p>\n<p></text>', '</div></body></text>')
        #search and set head-tags
        r = re.sub('#+(.+?)</p>','<head>\\1</head>', r)
        r = r.replace('<p><head>', '<head>')
        #set chapter tag above each head
        r = r.replace('<head>','</div>\n<div type ="chapter">\n<head>')
        # search for italic marks and set hi-tag
        r = re.sub('\*+(.+?)\*+', '<hi rend="italic">\\1</hi>', r)
        r = r.replace('<hi rend="italic">*</hi>', '***')
        #remember! you still need to make some edition, but not so much
        '''here is the place for experiments, uncomment what is useful for you'''
        #search footnotes that are marked as \[\]
        #r = re.sub(r'\\\[(.*?)\\\]', ' <ref target="N\\1"/>', r)
        # search footnotes that are marked as \{\}
        #r = re.sub('\*+\\\{(.*?)\\\}\*+', ' <ref target="N\\1"/>', r)
        #sometimes numbers are really digit, so you can use d
        #r =re.sub(r'\\\[(\d+)\\\]', '',r)
        # sometimes footnotes are marked with *
        # r = r.replace('*','<ref target="N1"/>')
        '''if your footnotes text is inside [text], you can gather all footnotes in a list and insert they at the end of the text'''
        #footnotes =re.findall(r'(\[.*?\])', r)
        #if it works, don´t forget to delete footnotes inside the text
        #r = re.sub(r'(\[.*?\])', '', r)
        #don`t forget to insert your footnotes at the end of the text
        #r = r+str(footnotes)
        #automatic generate filename
        name = os.path.basename(file).replace('txt','xml')
        fullname = os.path.join(save_path, name)
        #write text to file
        fa = open(fullname, 'w', encoding="utf8")
        fa.write(r)


def main():
    logging.basicConfig(level=logging.WARNING)

    prepare(SAVE_PATH)

    for src_file in Path(SOURCE_PATH).iterdir():
        if src_file.is_file() and src_file.name.endswith('.txt'):
            logging.debug(f'Processing {src_file}')
            text = open_file(src_file)
            text = clean_up(text)
            xml = transform(text)
            write_results(xml, SAVE_PATH, src_file.name)


if __name__ == '__main__':
    main()