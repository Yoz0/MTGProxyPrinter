#!/usr/bin/python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf
from pathlib import Path
import logging
from logging import info, warning, error

from input_reader import InputReader
from scryfall import Scryfall

SCALE = 100
CARD_WIDTH = 2.5 * SCALE
CARD_HEIGHT = 3.5 * SCALE
class Card(Gtk.Box):

    def __init__(self, image, callback):
        Gtk.Box.__init__(self)
        self.label = Gtk.Label()
        self.label.set_text("lol")
        self.image = []
        self.set_homogeneous(True)
        for i in image:
            loader = GdkPixbuf.PixbufLoader()
            loader.write(i)
            loader.close()
            pixbuf = loader.get_pixbuf().scale_simple(CARD_WIDTH, CARD_HEIGHT,
                    GdkPixbuf.InterpType.BILINEAR)
            self.image.append(Gtk.Image.new_from_pixbuf(pixbuf))
            self.add(self.image[-1])

        self.callback = callback


class ArtChooser(Gtk.VBox):

    def __init__(self, decklist):
        Gtk.VBox.__init__(self, spacing = 6)
        self.in_decklist = decklist
        self.out_decklist = []
        self.api = Scryfall(Path("cache"), "normal")
        
        scroll = Gtk.ScrolledWindow()
        self.card_box = Gtk.FlowBox()
        self.card_box.set_min_children_per_line(2)
        self.card_box.set_max_children_per_line(30)
        self.card_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        scroll.add(self.card_box)
        self.pack_start(scroll, True, True, 0)

        self._next_card()

        button_box = Gtk.Grid()
        button_box.attach(self._init_pass_button(), 0,0,1,1)
        button_box.attach(self._init_confirm_button(), 1,0,1,1)
        self.pack_end(button_box, False, False, 5)

    def _init_confirm_button(self):
        confirm_button = Gtk.Button.new_with_label("Confirm")
        confirm_button.connect("clicked", self._add_selected_card)
        return confirm_button

    def _init_pass_button(self):
        pass_button =  Gtk.Button.new_with_label("Pass")
        pass_button.connect("clicked", self._pass_card)
        return pass_button

    def _next_card(self):
        number, name, set_code, collector_number = self.in_decklist.pop()
        alternatives = self.api.get_alternatives(name, set_code,\
                collector_number) 
        if len(alternatives) == 1:
            info("Only one card found for {}".format(name))
            self._add_card(number, name, set_code, collector_number)
        elif len(alternatives) == 0:
            warning("{} can't be found".format(name))
            self._next_card()
        else:
            for (image, name, set_code, collector_number) in alternatives:
                callback = lambda: self._add_card(number, name, set_code,\
                        collector_number) 
                self.card_box.add(Card(image, callback))

    def _add_card(self, number, name, set_code, collector_number):
        self.out_decklist.append((number, name, set_code, collector_number))
        self._next_card()

    def _add_selected_card(self, widget):
        card = self.card_box.get_selected_children().pop().get_children().pop()
        card.callback()

    def _pass_card(self, widget):
        pass

        


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    window = Gtk.Window()
    input_reader = InputReader('|', '|')
    decklist = input_reader.get_decklist(Path("serra_angel.dec"))
    art_chooser = ArtChooser(decklist)
    window.add(art_chooser)
    window.show_all()
    window.connect("delete-event", Gtk.main_quit)
    Gtk.main()

