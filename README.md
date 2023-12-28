# lingolens

Search in Google Lens in lingo!

Tired of irrelevant results of reverse image search? Yeah, search results can be VERY different because of your language environment!

Lingolens allows:
- search image in Google Lens for several languages (RU/EN/PL by default), excluding known results
- generate one simple HTML report with all the results
- compare target image with result images!

## Example

Check example of search results: [report.html](report.html).

<img src="preview.png" width="800">

## Installation

Requests and bs4 are required.

```sh
pip3 install -r requirements.txt
```

## Usage

```sh
./lingolens.py example.jpg

Searching for example.jpg...
Searching in RU language...
Found 60 results
Searching in EN language...
Found 60 results
Skipped 1 already known images
Searching in PL language...
Found 60 results
Skipped 1 already known images
```

You should specify languages in file `langs.txt` in the following format:
```
ru
en
pl
```

The full list of supported languages is [here](https://developers.google.com/custom-search/docs/xml_results_appendices?hl=en#interfaceLanguages).

## TODO

- [x] Customization of language list for a search (simple config file)
- [x] Language filter in a report
- [ ] Standalone exe-file for Windows

## Credits

Thanks to BLACK for inspiration and support!

Designed and developed for solving tasks on [OSINT investigation forum](https://t.me/+GMxoDCvLO0k0MWRi).

