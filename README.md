# MTGProxyPrinter
A tool to create proxy sheet of card from the game Magic: The Gathering

### Requirements
* Linux 
* Python 3.5 and up
* [requests](http://docs.python-requests.org/en/master/)
* [reportlab](https://www.reportlab.com/)

## Usage
run `./main -h` for the help

## Input
The input should be a text file with the name of one card per line.

Empty line and line starting with `//` will be ignored. Please note
that a line with `//` in the middle will not be ignored. 

Each none empty line should look like one of this :
* Serra Angel
* Archangel Avacyn
* Serra Angel | ME4
* Very Cryptic Command | UST | 49a

You can also add the number of copies you want at the beginning of the line.
 If the card is double faced, you can write only the first name.  

The complete syntax is the following :

`[Number of copies] name [| set_code [| collector_number]]`

## Features to come

- [ ] A nice GUI
- [ ] An artwork chooser
- [ ] Multi-threading on card request
 
## Contributing
Pull requests are welcome. For major changes, please open an issue
first to discuss what you would like to change.

## Notes
The card images are gathered on [Scryfall](https://scryfall.com/). Thanks Scryfall :) 
