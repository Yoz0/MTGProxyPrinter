#!/usr/bin/python3

import os
import logging
from logging import info, debug, warning, error
import argparse
from argparse import ArgumentParser
from pathlib import Path

from scryfall import Scryfall
from input_reader import InputReader
from pprint import pprint

def main():
    api = Scryfall(Path('cache'), 'large')
    input_reader = InputReader('|','|')
    decklist = input_reader.get_decklist(Path('serra_angel.dec'))

    cards = {'cards':[]}
    for (number, name, set_code, collector_number) in decklist:
        alternatives = api.get_alternatives(name, set_code, collector_number)
        card = {'name':name, 'count':number, 'alternatives':[]}
        for (set_code, collector_number, url_front, url_back) in alternatives:
            alternative = {'set':set_code, 'no':collector_number,
                    'url':url_front, 'url_back':url_back}
            card['alternatives'].append(alternative)
        cards['cards'].append(card) 
    pprint(cards)
    return 0
if __name__ == '__main__':
    res = main()
    exit(res)
