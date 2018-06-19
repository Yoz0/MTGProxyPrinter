#!/usr/bin/python3


import os
import logging
from logging import info, debug, warning, error
import argparse
from argparse import ArgumentParser
from pathlib import Path

from scryfall import Scryfall
from mtg_printer import MtgPrinter
from input_reader import InputReader


def parse_arguments():
    parser = ArgumentParser(description="MTGProxyPrinter, to create proxy \
            sheet from deck or cube list")
    parser.add_argument('input', type=str, help="The input filename")
    parser.add_argument('--out', metavar='output', type=str, default=None,
                        help="The output filename (default: same as input)")
    parser.add_argument('--cache', metavar='cache', type=str, default='cache',
                        help="The cache directory (default: cache/)")
    parser.add_argument('--img', metavar='version', type=str, default='large',
                        help="The version of the image that will be fetch from \
                        Scryfall, choose from : large (default), png, normal \
                        and small")
    parser.add_argument('-v', action='store_true', help="Activate verbose mode")
    parser.add_argument('--set-delimiter', type=str, default="|",
                        help="The character used to separate the name and the \
                        set code, default is |")
    parser.add_argument('--collector-delimiter', type=str, default='|',
                        help="The character used to separate the set code and \
                        the collector number, default is |")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not (input_path.exists() and input_path.is_file()):
        error("The input file does not exists, or is not a file")
        exit(1)

    output_filename = args.out
    if output_filename is None:
        output_filename = input_path.name.split('.')[0] + '.pdf'
    if output_filename.split('.')[-1] != 'pdf':
        output_filename += ".pdf"

    cache_path = Path(args.cache)
    if cache_path.exists() and cache_path.is_file():
        error("{} is a file, not a directory".format(cache_path.name))
        exit(1)

    version = args.img
    if version not in ["large", "normal", "small", "png"]:
        error("{} is not an accepted image version")
        exit(1)

    verbose = args.v
    set_delimiter = args.set_delimiter
    collector_delimiter = args.collector_delimiter

    return (input_path, output_filename, cache_path, version, verbose,\
            set_delimiter, collector_delimiter)

def download_cards_from_decklist(decklist, api):
    for (number, name, set_code, collector_number) in decklist:
        res = api.get_card(name, set_code, collector_number)
        if res == None:
            return 1
    return 0

def print_decklist(decklist, api, pdf_file):
    for (number, name, set_code, collector_number) in decklist:
        images = api.get_card(name, set_code, collector_number)
        if images is None:
            return 1
        info("Adding image of {}" .format(name))
        for _ in range(number):
            pdf_file.add_images(images)
    pdf_file.save()
    return 0

def main():
    input_path, output_filename, cache_path, img_version, verbose,\
            set_delimiter, collector_delimiter = parse_arguments()
    if verbose:
        logging.basicConfig(level=logging.INFO)
    info("Starting program")

    api = Scryfall(cache_path, img_version)
    input_reader = InputReader(set_delimiter, collector_delimiter)
    decklist = input_reader.get_decklist(input_path)
    if download_cards_from_decklist(decklist, api) > 0:
        error("Something went wrong when downloading")
        return 1

    pdf_file = MtgPrinter(output_filename)
    if print_decklist(decklist, api, pdf_file) > 0:
        error("Something went wrong when doing the pdf")
        return 1
    return 0

if __name__ == '__main__':
    res = main()
    exit(res)
