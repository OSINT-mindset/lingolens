# lingolens

Search in Google Lens in lingo!

Tired of irrelevant results of reverse image search? Yeah, search results can be VERY different!

Lingolens allows:
- search image in Google Lens for several languages (RU/EN/PL for now), excluding known results
- generate one simple HTML report with all the results
- compare target image with result images!

## Example

Check example of search results: [report.html](report.html).

<img src="preview.png" width="800">

## Installation

Only requests lib is required.

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

## TODO

- [ ] Customization of language list for a search (simple config file)
- [ ] Language filter in a report
- [ ] Standalone exe-file for Windows

## Credits

Thanks to BLACK for inspiration and support!

Designed and developed for solving tasks on [OSINT investigation forum](https://t.me/+GMxoDCvLO0k0MWRi).

