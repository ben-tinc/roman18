'''This Script generate an xml-file from txt-data'''

import os.path
import glob
import logging
from pathlib import Path
import re

#set a path where your data are saved
SOURCE_PATH = "../../plain/epubs/"
#set a path where you want to save your data
SAVE_PATH = 'epubs_xmls/'


def prepare(save_path):
    """Ensure that the configured save directory exists."""
    p = Path(save_path)
    p.mkdir(parents=True, exist_ok=True)
    
    if not any(p.iterdir()):
        msg = f'SAVE_PATH "{p.absolute()}" is not empty, we might override previous results.'
        logging.warning(msg)
    
    return p


def open_file(path):
    with open(path, encoding='utf-8') as f:
        text = f.read()
    return text


def clean_up(text):
    # Delete unnecessary data.
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
    prepare(SAVE_PATH)

    for src_file in Path(SOURCE_PATH).iterdir():
        if src_file.is_file() and src_file.name.endswith('.txt'):
            text = open_file(src_file)
            text = clean_up(text)


if __name__ == '__main__':
    main()