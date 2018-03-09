#!/usr/bin/python3

import os
import logging
from logging import info, debug, warning, error
import argparse
from argparse import ArgumentParser
from pathlib import Path
from scryfall import Scryfall
from mtg_printer import MtgPrinter


VERSION_DELIMITER = "|"
SET_CODE_DELIMITER = "|"


def is_ignored(line):
    return line.strip() == "" or line.strip()[:2] == "//"

def retrieve_number(line):
    number_string, i, line = "", 0, line.strip()
    while line[i].isdigit():
        number_string += line[i]
        i += 1
    if number_string == "":
       return 1
    else:
       return int(number_string)

def parse_line(line):
    line = line.strip()
    number = retrieve_number(line)
    line = line.lstrip('0123456789 ')
    if not VERSION_DELIMITER in line:
        return (number, line, None, None)
    name, version = line.split(VERSION_DELIMITER, maxsplit=1)
    if not SET_CODE_DELIMITER in version:
        return (number, name.strip(), version.strip().lower(), None)
    set_code, collector_number = version.split(SET_CODE_DELIMITER, maxsplit=1)
    return (number, name.strip(), set_code.strip().lower(), 
            collector_number.strip().lower())

def parse_arguments():
    parser = ArgumentParser(description="MTGProxyPrinter, to create proxy \
            sheet from deck or cube list")
    parser.add_argument('input', type=str,
            help="The input filename")
    parser.add_argument('--out', metavar='output', type=str, default=None,
            help="The output filename (default: same as input)")
    parser.add_argument('--cache', metavar='cache', type=str, default='cache',
            help="The cache directory (default: cache/)")
    parser.add_argument('--img', metavar='version', type=str, default='large',
            help="The version of the image that will be fetch from Scryfall, \
                  choose from : large (default), png, normal and small")
    parser.add_argument('-v', action='store_true',
            help = "Activate verbose mode")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not (input_path.exists() and input_path.is_file()):
        error("The input file does not exists, or is not a file")
        exit(1)

    output_filename = args.out
    if output_filename == None:
        output_filename = input_path.name.split('.')[0] + '.pdf'
    if output_filename.split('.')[-1] != 'pdf':
        output_filename += ".pdf"
        

    cache_path = Path(args.cache)
    if cache_path.exists() and cache_path.is_file():
        error("{} is a file, not a directory".format(cache_path.name))
        exit(1)

    version = args.img
    if not version in ["large", "normal", "small", "png"]:
        error("{} is not an accepted image version")
        exit(1)

    verbose = args.v

    return (input_path, output_filename, cache_path, version, verbose)

def download_cards_from_decklist(input_path, cache_path, img_version):
    api = Scryfall(cache_path, img_version)
    with input_path.open('r') as deck:
        for line in deck:
            if is_ignored(line): continue
            number, name, set_code, collector_number = parse_line(line)
            #TODO: Add verification on name, set_code and collector_number
            #to avoid code injection and other nasty stuff
            res = api.get_card(name, set_code, collector_number)
            if res == None:
                return 1
    return 0

def print_decklist(input_path, output_filename, cache_path, img_version):
    pdf_file = MtgPrinter(output_filename)
    api = Scryfall(cache_path, img_version)
    with input_path.open('r') as deck:
        for line in deck:
            if is_ignored(line): continue
            number, name, set_code, collector_number = parse_line(line)
            #TODO Add verifications
            images = api.get_card(name, set_code, collector_number)
            if images == None:
                return 1
            info("Adding image of {}" .format(name))
            for i in range(number):
                pdf_file.add_images(images)
    pdf_file.save()
    return 0

def main():
    input_path, output_filename, cache_path, img_version, verbose = \
            parse_arguments()
    if verbose:
        logging.basicConfig(level=logging.INFO)
    info("Starting program")
    if download_cards_from_decklist(input_path, cache_path, img_version) > 0:
        error("Something went wrong when downloading")
        exit(1)
    if print_decklist(input_path, output_filename, cache_path, img_version) > 0:
        error("Something went wrong when doing the pdf")
        exit(1)
    exit(0)

if __name__ == '__main__':
    main()
