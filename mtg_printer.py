import logging
from logging import info, error, debug, warning
import os
from pathlib import Path
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from PIL import Image

CARDS_PER_ROW = 3
ROWS_PER_PAGE = 3

OUTPUT_PAGESIZE = A4
PAGE_WIDTH, PAGE_HEIGHT = OUTPUT_PAGESIZE
CARD_WIDTH = 2.5 * inch
CARD_HEIGHT = 3.5 * inch
MARGIN_LEFT = (PAGE_WIDTH - CARDS_PER_ROW * CARD_WIDTH) / 2
MARGIN_TOP = 0.6 * inch
SPACE_BETWEEN = 0 * inch

class MtgPrinter(object):
    def __init__(self, output_file):
        self.output_file = output_file
        self.canvas = Canvas(output_file, OUTPUT_PAGESIZE)
        self.column = 0
        self.row = 0

    def _add_image(self, image):
        x = MARGIN_LEFT + self.column * (CARD_WIDTH + SPACE_BETWEEN)
        y = PAGE_HEIGHT - MARGIN_TOP - CARD_HEIGHT - \
                self.row * (CARD_HEIGHT + SPACE_BETWEEN)
        self.canvas.drawImage(image, x, y, width=CARD_WIDTH, height=CARD_HEIGHT)
        self._update_coordinate()

    def _update_coordinate(self):
        if self.column < CARDS_PER_ROW - 1:
            self.column += 1
        elif self.row < ROWS_PER_PAGE - 1:
            self.row += 1
            self.column = 0
        else:
            self.row, self.column = 0, 0
            self.canvas.showPage() # This page is full add another one

    # Public functions

    def add_images(self, images_path):
        for image_path in images_path:
            image = Image.open(image_path)
            image_reader = ImageReader(image)
            self._add_image(image_reader)

    def save(self):
        self.canvas.save()
