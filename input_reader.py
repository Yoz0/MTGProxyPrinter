from pathlib import Path



class InputReader(object):

    def __init__(self, set_delimiter, collector_delimiter):
        self.set_delimiter = set_delimiter
        self.collector_delimiter = collector_delimiter

    def _is_ignored(self, line):
        return line.strip() == "" or line.strip()[:2] == "//"

    def _retrieve_number(self, line):
        number_string, i, line = "", 0, line.strip()
        while line[i].isdigit():
            number_string += line[i]
            i += 1
        if number_string == "":
           return 1
        else:
           return int(number_string)

    def _parse_line(self, line):
        line = line.strip()
        number = self._retrieve_number(line)
        line = line.lstrip('0123456789 ')
        if not self.set_delimiter in line:
            return (number, line, None, None)
        name, version = line.split(self.set_delimiter, maxsplit=1)
        if not self.collector_delimiter in version:
            return (number, name.strip(), version.strip().lower(), None)
        set_code, collector_number = version.split(self.collector_delimiter,
                maxsplit=1)
        return (number, name.strip(), set_code.strip().lower(), 
                collector_number.strip().lower())

    def get_decklist(self, deck_path):
        """
        deck_path should be of the type Path
        Return the decklist as a list of form :
        [(number, name, set_code, collector_number), ...]
        if any of this is not precised in the file it will be None 
        """
        decklist = []
        with deck_path.open() as deck:
            for line in deck:
                if self._is_ignored(line): continue
                #TODO: check the line for stuff
                decklist.append(self._parse_line(line))
        return decklist
