'''
This Script generates an xml-file from txt-data.
'''

import xml.etree.ElementTree as ET
import os.path
import glob
from itertools import takewhile
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
    lines = [line for line in text.split('\n') if line.strip()]
    # Delete all lines after '# ****À propos de cette édition électronique'
    lines = takewhile(lambda l: not l.startswith('# ****À propos de cette édition électronique'), lines)

    text = '\n'.join(lines)
    return text


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
    chapters = split_chapters(text)
    body = ET.Element('body')
    footnotes = {}

    for chapter in chapters:
        markup, footnotes = build_chapter_xml(chapter, footnotes)

    # If we are currently inside a div, keep track of it.
    div = None
    # Collect all the footnotes along the way.
    notes = {}
  
    return body


def build_chapter_xml(chapter, footnotes):
    '''Given the text of one chapter, create the appropriate XML markup.'''
    
    offset = max(footnotes.keys()) or 0
    text, notes = parse_footnotes(chapter, offset)
    footnotes.update(notes)

    markup = ET.Element('div', attrib={'type': 'chapter'})
    
    for line in text.split('\n'):
        if line.startswith('#'):            
            node = ET.SubElement(markup, 'head')
            node.text = line.replace('#', '').strip()
        elif line:
            node = ET.SubElement(markup, 'p')
            node.text = line.strip()
        
        # Insert additional markup inside the new node.
        node = insert_fn_markers_xml(node)
        node = insert_italics_xml(node)

    return markup, footnotes


def insert_fn_markers_xml(paragraph):
    '''Update paragraph with <ref> nodes for the footnote markers.
    
    This relies on the numerical markers being correct, i.e. if footnotes are
    numbered for each chapter individually, they should have been corrected
    with `parse_footnotes()` beforehand.
    '''
    mark_pattern = r'\\\[(\d+)\\\]'
    segments = re.split(mark_pattern, paragraph.text)

    # Check if there are actually footnote markers in this paragraph.
    if len(segments) > 1:
        last_node = paragraph
        i = 0
        while i < len(segments):
            segment = segments[i]
            # Text at the start of the paragraph. This is stored in the `text` property
            # of the paragraph node itself.
            if not segment.isnumeric() and i == 0:
                paragraph.text = segment
            # Marker segment. This is stored as a `ref` child node without `text`. 
            # Further text will be appended to the `tail` property of this node.
            elif segment.isnumeric():
                number = f'#N{segment}'
                fn_node = ET.SubElement(paragraph, 'ref', attrib={'target': number})
                last_node = fn_node
            # Regular text content after at least one `ref` has been created.
            # Store it as the `tail` property of the latest `ref` node.
            else:
                last_node.tail = segment
            i += 1

    return paragraph


def insert_italics_xml(paragraph):
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


def parse_footnotes(text, fn_offset=0):
    '''Given a string, identify footnotes and replace their markers.
    
    Sometimes, footnotes in a document are numbered per chapter. In the final
    TEI, we put all the footnotes in a designated <back> section. So we need to
    renumber them first. The parameter `fn_offset` gives the number of footnotes
    we have already seen in previous chapters.
    '''
    mark_pattern = r'(\\\[)(\d+)(\\\])'
    markers = [m[1] for m in re.findall(mark_pattern, text)]
    notes = [re.search(f'\n{n}\.\s↑\s+(.*?)\s*\n', text).group(1) for n in markers]

    # Replace markers with updated numbering based of offset of this chapter.
    text = re.sub(
        mark_pattern,
        lambda match: f'{match.group(1)}{(int(match.group(2))+fn_offset)}{match.group(3)}',
        text)
    # Delete actual notes at the end of the chapter. They will eventually be inserted
    # in the <back> of the document.
    text = re.sub(r'\d+?\.\s↑\s+(.*?)\s*?\n', '', text)

    # Map updated markers to corresponding footnote text.
    footnotes = {int(m)+fn_offset: n for m, n in zip(markers, notes)}

    return text, footnotes


def split_titlepage(text):
    '''Split on the second occurence of "### ".'''
    # How to recognize the end of the titlepage
    marker = '\n### '
    end_of_titlepage = text.find(marker, text.find(marker)+len(marker))
    # Add 1 to index so that the newline still belongs to the titlepage.
    titlepage, rest = text[:end_of_titlepage+1], text[end_of_titlepage+1:]
    return titlepage, rest


def split_chapters(text):
    '''Split on occurrences of "### ".
    
    The main reason why we want to process chapters individually is because footnotes
    are internally numbered per chapter.
    '''
    pattern = r'(###\s.+?)\s*\n'
    segments = [s for s in re.split(pattern, text) if s]

    # No chapters:
    if len(segments) == 1:
        chapters = [text]
    # Segments start with chapter heading:
    elif segments[0].startswith('### '):
        chapters = [f'{h}\n{t}' for h, t in zip(segments[0::2], segments[1::2])]
    # Segments start with chapter without heading:
    else:
        chapters = [segments[0]]
        chapters.extend([f'{h}\n{t}' for h, t in zip(segments[1::2], segments[2::2])])

    return chapters


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
    text = 'Text \[1\] text \[2\] text.\n\n1. ↑ http://fr.wikisource.org\n2. ↑  http://fr.wikisource.org\n'
    res_text, res_fns = parse_footnotes(text)
    #main()