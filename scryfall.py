import requests
import logging
from logging import info, error, warning, debug
import shutil
from pathlib import Path
from PIL import Image
from io import BytesIO

SF_ENDPOINT = "https://api.scryfall.com/"
SF_ENDPOINT = SF_ENDPOINT + "cards/"
INDEX_DELIMITER = "&"
UNIQUE = "art"
# UNIQUE = "prints"

class Scryfall(object):
    def __init__(self, cache_directory, image_version):
        self.image_version = image_version
        self.cache_directory = cache_directory
        self.index_path = cache_directory / "index.txt"
        if self._init_cache() > 0:
            exit(1)         #TODO: This is ugly, it should be done differently

    def _init_cache(self):
        if self.cache_directory.is_file():
            error("{} is a file, not a directory".format(
                self.cache_directory.name))
            return 1
        if not self.cache_directory.exists():
            self.cache_directory.mkdir()
        if self.index_path.is_dir():
            error("{} is a directory, not a file".format(self.index_path.name))
            return 1
        return 0

    def _is_double_faced(self, card):
        return card["layout"] == "transform"

    def _is_same_card(self, name, set_code, collector_number, card_properties):
        if set_code == None:
            card_name = card_properties[0]
            return name == card_name or name + " // " in card_name
        elif collector_number == None:
            card_name = card_properties[0]
            card_set_code = card_properties[1]
            return (name == card_name or name + " // " in card_name) and \
                    set_code == card_set_code
        else:
            card_set_code = card_properties[1]
            card_collector_number = card_properties[2]
            return card_set_code == set_code and \
                    card_collector_number == collector_number

    def _log_name(self, name, set_code, collector_number):
        delimiter = " | "
        if set_code == None:
            return name
        elif collector_number == None:
            return name + delimiter + set_code
        else:
            return name + delimiter + set_code + delimiter + collector_number

    def _card_log_name(self, card):
        return self._log_name(card["name"], card["set"],
                card["collector_number"])

    def _request_alternatives(self, name, set_code, collector_number):
        if set_code == None:
            return requests.get(SF_ENDPOINT + "search?q=" + name\
                    + "&unique=" + UNIQUE)
        elif collector_number == None:
            return requests.get(SF_ENDPOINT + "search?q=" + name\
                    + "+set=" + set_code + "&unique=" + UNIQUE)
        else:
            return requests.get(SF_ENDPOINT + "search?"\
                    + "set:" + set_code + "+cn:" + collector_number\
                    + "&unique=" + UNIQUE)

    def _request_card(self, name, set_code, collector_number):
        if set_code == None:
            return requests.get(SF_ENDPOINT + "named?exact=" + name)
        elif collector_number == None:
            return requests.get(SF_ENDPOINT + "named?exact=" + name
                    + "&set=" + set_code)
        else:
            return requests.get(SF_ENDPOINT + set_code + "/" + collector_number)

    def _request_image(self, card):
        """
        Get the image of the card
        return the image if the card is simple faced,
        return both image if the card is double faced
        """
        if self._is_double_faced(card):
            url_front = card["card_faces"][0]["image_uris"] [self.image_version]
            url_back = card["card_faces"][1]["image_uris"][self.image_version]
            r_front = requests.get(url_front, stream=True)
            r_back = requests.get(url_back, stream=True)
            return [r_front, r_back]
        url = card["image_uris"][self.image_version]
        return [requests.get(url, stream=True)]

    def _handle_errors(self, response):
        res = 0
        if response.status_code == 404:
            error("The response was not found")
            res = 1
        if response.status_code == 429:
            error("Too many requests, please be slower")
            res = 1
        if response.status_code != 200:
            error("Unexpected error {}".format(response.status_code))
            res = 1
        if res == 1:
            if 'warnings' in response.json() and\
                    response.json()['warnings'] != None:
                for w in response.json()['warnings']:
                    warning(w)
            error(response.json()['details'])
        return res

    def _cache_image(self, card, images):
        """ Cache the card image, then return the path to the image"""
        self._add_image_to_index(card)
        name = card["name"].replace('/','_')
        set_code = card["set"]
        collector_number = card["collector_number"]
        if self._is_double_faced(card):
            front_path = self.cache_directory /\
                    "{}_{}_front.jpg".format(set_code, collector_number)
            back_path = self.cache_directory /\
                    "{}_{}_back.jpg".format(set_code, collector_number)
            info("Caching {} from {}".format(name, set_code))
            with front_path.open('wb') as outfile:
                    shutil.copyfileobj(images[0].raw, outfile)
            with back_path.open('wb') as outfile:
                    shutil.copyfileobj(images[1].raw, outfile)
            return [front_path, back_path]
        else:
            file_path = self.cache_directory /\
                    "{}_{}.jpg".format(set_code, collector_number)
            with file_path.open('wb') as outfile:
                    shutil.copyfileobj(images[0].raw, outfile)
            return [file_path]

    def _add_image_to_index(self, card):
        with self.index_path.open('a') as index:
            line = card["name"] + INDEX_DELIMITER
            line += card["set"] + INDEX_DELIMITER
            line += card["collector_number"] + INDEX_DELIMITER
            if self._is_double_faced(card):
                line += "Yes" + INDEX_DELIMITER
                line += "{}_{}_front.jpg"\
                        .format(card["set"], card["collector_number"]) +\
                        INDEX_DELIMITER
                line += "{}_{}_back.jpg"\
                        .format(card["set"], card["collector_number"])
            else:
                line += "No" + INDEX_DELIMITER
                line += "{}_{}.jpg"\
                        .format(card["set"], card["collector_number"]) +\
                        INDEX_DELIMITER
            index.write(line + "\n")
        return 0

    def _is_cached(self, name, set_code, collector_number):
        if not self.index_path.exists():
            return False
        with self.index_path.open('r') as index:
            for line in index.readlines():
                card_properties = line.strip().split(INDEX_DELIMITER)
                # [name, set_code, collector_number, is_dfc, front_img, back_img]
                if self._is_same_card(name, set_code, collector_number,
                        card_properties):
                    return True
        return False

    def _get_cached(self, name, set_code, collector_number):
        if not self.index_path.exists():
            error("No index file found")
            return None
        with self.index_path.open('r') as index:
            for line in index.readlines():
                card_properties = line.strip().split(INDEX_DELIMITER)
                # [name, set_code, collector_number, is_dfc, front_img, back_img]
                if self._is_same_card(name, set_code, collector_number,
                        card_properties):
                    if card_properties[3] == "Yes": # if the card is double-faced
                        return [self.cache_directory / card_properties[4],\
                                self.cache_directory / card_properties[5]]
                    else:
                        return [self.cache_directory / card_properties[4]]
        error("The card was not found in cache")
        return None

    def _download(self, card):
        image = self._request_image(card)
        return self._cache_image(card, image)

    def _download_all(self, cards):
        res = []
        for card in cards['data']:
            image = []
            for i in self._request_image(card):
                image.append(i.content)
            res.append((image, card['name'], card['set'],\
                    card['collector_number']))
        if cards['has_more']:
            response = requests.get(cards['next_page'])
            if self._handle_errors(response) != 0:
                error("Could not download the next page of a big response set.\
                       This is weird...")
            next_cards = response.json()
            res += self.download_all(next_cards)
        return res

    ### Public methods ###

    def get_card(self, name, set_code, collector_number):
        """
        Get the card on Scryfall with the specified name.
        Search for the card in the set specified by set_code if provided.
        Cache the image in the cache directory.
        Return 1 if something wrong happened, 0 otherwise.
        """
        if name == None or name.strip() == "":
            error("No name found !")
            return None
        log_name = self._log_name(name, set_code, collector_number)
        if self._is_cached(name, set_code, collector_number):
            info("{} was already in cache".format(log_name))
            return self._get_cached(name, set_code, collector_number)
        info("Starting to download {}".format(log_name))
        response = self._request_card(name, set_code, collector_number)
        if self._handle_errors(response) != 0:
            error("Could not download {}".format(log_name))
            return None
        card = response.json()
        if card["name"] != name:
            warning(("Found this card : {} \n" + \
                    "It's different from what's written on the file : {}")
                .format(self._card_log_name(card), log_name))
        return self._download(card)

    def get_alternatives(self, name, set_code, collector_number):
        """
        Get all the cards corresponding to the name, set and number.
        Return all the image with the name, set and number.
        (image, name, set_code, collector_number)
        """
        if name == None or name.strip() == "":
            error("No name found !")
            return []
        log_name = self._log_name(name, set_code, collector_number)
        info("Starting to download {}".format(log_name))
        response = self._request_alternatives(name, set_code, collector_number)
        if self._handle_errors(response) != 0:
            error("Could not download the alternatives of {}".format(log_name))
            return []
        cards = response.json()
        alternatives = self._download_all(cards)
        return alternatives

