# lingolens

Search in Google Lens in lingo!

Tired of irrelevant results of reverse image search? Yeah, search results can be VERY different because of your language environment!

Lingolens allows:
- search images in Google Lens with specific languages and countries, excluding known results
- generate one simple HTML report with all the results
- provide you a possibility to compare the target image with the result images
- a pretty user interface is supported!

## User interface

<img src="https://github.com/OSINT-mindset/lingolens/assets/31013580/5c312ade-25e7-43cd-8d8e-354e6c1bdc15" width="500">

## Report example

Check example of search results: [report.html](report.html).

<img src="preview.png" width="800">

## Installation

Requests and bs4 are required for the CLI version of the tool. Streamlit is required for User Interface.

```sh
pip3 install -r requirements.txt
```

## Usage

As CLI tool:
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
You will get the report file in the same folder.

Before you should specify languages in the file `langs.txt` in the following format:
```
ru
en
pl
```

As a browser-based tool:
```sh
streamlit run web_search.py
```

By default, Streamlit create a local application http://localhost:8501/. You can try to deploy it on cloud infrastructure, but Google will very quickly ask script for captcha.

Then just choose the appropriate languages (mandatory) and countries (optional) and upload your image. 
To download the report click the button "Download report"

<img width="300" src="https://github.com/OSINT-mindset/lingolens/assets/31013580/af307158-9bb1-4835-af3f-751ecfac8670">

The full list of supported languages and countries is [here](https://developers.google.com/custom-search/docs/xml_results_appendices?hl=en#interfaceLanguages).

## TODO

- [x] Customization of language list for a search (simple config file)
- [x] Language filter in a report
- [ ] Standalone exe-file for Windows
- [ ] Checkbox for switching to thumbnails instead of full images
- [ ] Validation of lang-country combinations

## Credits

Thanks to BLACK for inspiration and support!

Designed and developed for solving tasks on [OSINT investigation forum](https://t.me/+GMxoDCvLO0k0MWRi).

