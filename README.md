# lingolens

Search in Google Lens in lingo!

Tired of irrelevant results of reverse image search? Yeah, search results can be VERY different because of your language environment!

Lingolens allows:
- search images in Google Lens with specific languages and countries, excluding known results
- visually select a region of the image to search (optional)
- generate one HTML report with all the results
- compare the target image with the result images via a sticky preview
- a pretty user interface is supported!

The full list of supported languages and countries is [here](https://developers.google.com/custom-search/docs/xml_results_appendices?hl=en#interfaceLanguages).

## How it works

Google Lens used to return server-rendered HTML for the upload endpoint, so a plain `requests.post` was enough. That's no longer the case — Lens now requires a JavaScript-capable client and aggressively detects bots. So lingolens drives a real Chromium instance via [Playwright](https://playwright.dev/python/) with stealth patches and a persistent profile (cookies are reused, captcha state survives between runs).

For each selected language, a fresh browser context with that `locale=` is opened. This makes the JS upload request honour the locale (`hl=ko`, `Accept-Language: ko-KR`, `navigator.language` etc.) and Google really returns different result sets across languages.

## User interface

<img src="https://github.com/OSINT-mindset/lingolens/assets/31013580/5c312ade-25e7-43cd-8d8e-354e6c1bdc15" width="500">

## Report example

Check example of search results: [report.html](report.html).

<img src="preview.png" width="800">

## Installation

```sh
pip3 install -r requirements.txt
playwright install chromium
```

The second command downloads the Chromium build Playwright drives (~150 MB, one-off).

## Usage

### As a browser-based tool

```sh
streamlit run web_search.py
```

Streamlit serves the UI at http://localhost:8501/. Pick languages (mandatory) and countries (optional), upload an image. Optionally toggle **Select a region of the image to search** — drag a box on the image, then **double-click inside the box** to apply the crop. Then press **Search in Google Lens with selected languages**.

While the search runs you'll see a live status panel with per-language progress (`KO: 33 total on page, 15 new (rest already seen)`). After it finishes you get:

- a **Download report** button (full HTML report),
- a 3-column gallery of result thumbnails with `[LANG]` tags and links to source pages,
- a sticky preview of the original/cropped image in the bottom-right, so you can visually compare while scrolling.

#### First-run captcha

The very first time Lens may show a captcha. If that happens, run once with:

```sh
LINGOLENS_HEADLESS=0 streamlit run web_search.py
```

This makes the Chromium window visible — solve the captcha manually. Cookies are stored in `~/.lingolens-profile`, so subsequent runs in default (headless) mode reuse them and shouldn't trigger captcha again.

### As CLI tool

```sh
./lingolens.py example.jpg
```

You will get the `report.html` file in the same folder.

Languages are read from `langs.txt`, one per line:

```
ru
en
pl
```

### Environment variables

| Variable | Default | What it does |
| --- | --- | --- |
| `LINGOLENS_HEADLESS` | `1` | `0` to show the Chromium window (useful for solving captcha) |
| `LINGOLENS_PROFILE_DIR` | `~/.lingolens-profile` | Where Playwright stores its persistent profile (cookies, captcha state) |

## TODO

- [x] Customization of language list for a search (simple config file)
- [x] Language filter in a report
- [x] Visual region selection (crop)
- [x] Inline gallery and sticky original preview in the Streamlit UI
- [ ] Standalone exe-file for Windows
- [ ] Checkbox for switching to thumbnails instead of full images
- [ ] Validation of lang-country combinations
- [ ] Automatic captcha-solving fallback

## Credits

Thanks to BLACK for inspiration and support!

Designed and developed for solving tasks on [OSINT investigation forum](https://t.me/+GMxoDCvLO0k0MWRi).
