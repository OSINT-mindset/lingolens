#!/usr/bin/env python3
import math
import random
import re
import sys
from base64 import b64encode
from urllib.parse import unquote
import requests


class LensPic:
    url: str
    site: str
    lang: str

    def __init__(self, u, s, l):
        self.url = u
        self.site = s
        self.lang = l

    def __hash__(self):
        return id(self) if not self.url else hash(self.url+self.site)

    def __eq__(self, other):
        return self.url+self.site == other.url+other.site


# https://github.com/typeling1578/Search-on-Google-Lens/blob/af04f2c01dd6f93b163b561807cb4597813c3ab4/background.js
def generateRandomString(n):
    s = "abcdefghijklmnopqrstuvwxyz0123456789"
    str = ""
    for _ in range(n):
        str += s[math.floor(random.random() * len(s))]
    return str


def get_google_lens_url(imageFile, lang):
    body = {
        "image_url": "https://" + generateRandomString(12) + ".com/" + generateRandomString(12),
        "sbisrc": "Chromium 98.0.4725.0 Windows"
    }
    files = {'encoded_image': imageFile}
    language = f'&hl={lang}&lr={lang}'
    result = requests.post(f'https://lens.google.com/upload?{language}&ep=ccm&s=&st=' + generateRandomString(12), data=body, files=files)
    if result.status_code == 200:
        # print(result.text)
        matches = re.findall(r"https?:\/\/[-_.!~*\'()a-zA-Z0-9;\/?:\@&=+\$,%#]+", result.text)
        if matches:
            url = matches[0]
            return url


def get_lens_previews(image_filename, lang):
    f = open(image_filename, mode='rb')
    search_url = get_google_lens_url(f, lang)

    results_html = requests.get(search_url).text
    matches = re.findall(r'"https://www.google.com/imgres\?imgurl.+?"', results_html)
    if matches:
        return matches

    return []


def get_site_preview_urls_pair(lens_preview_url):
    decoded_url = lens_preview_url.encode().decode('unicode-escape')

    preview_url_str = re.search(r'.*imgurl=(.+?)&.*', decoded_url).groups(0)
    preview_url = unquote(preview_url_str[0])

    site_url = re.search(r'.*imgrefurl=(.+?)&.*', decoded_url).groups(0)[0]
    return (site_url, preview_url)


def get_base64_image(url):
    r = requests.get(url, stream=True)
    img_uri = ("data:" +
           r.headers['Content-Type'] + ";" +
           "base64," + b64encode(r.content).decode())

    return img_uri


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('./lingolens.py <image filename>')
        sys.exit(1)

    filename = sys.argv[1]
    print(f'Searching for {filename}...')

    all_pics = []

    langs = [
        'ru',
        'en',
        'pl'
    ]

    html_text = """
        <html>
        <title>Results of Google Lens search</title>
        <style>
            html{
              background-color: #d0d2d2;
            }
            p {
              display: inline-block;
              text-overflow: ellipsis;
              margin: 10px;
            }
            img {
              max-width: 400px;
              max-height: 400px;            
            }
            img.result {
              display: block;
              border: 1px solid black;
            }
            img.target {
              display: block;
              position: fixed;
              right: 20;
              bottom: 20;
              border: 2px solid red;
            }
            a {
              width: 400px;
              overflow: hidden;
              display: block;
              white-space: nowrap;
            }
            a span {
                color: red;
            }
        </style>
        <body>
    """

    img_type = 'image/png' if filename.endswith('.png') else 'image/jpeg'

    with open(filename, 'rb') as image_file:
        img_decoded = b64encode(image_file.read()).decode()
        img_uri = f"data:{img_type};base64,{img_decoded}"
        html_text += f'<img class="target" src="{img_uri}">'

    for l in langs:
        print(f'Searching in {l.upper()} language...')
        previews = get_lens_previews(filename, l)
        print(f'Found {len(previews)} results')

        skipped = 0
        for p in previews:
            pair = get_site_preview_urls_pair(p)
            pic = LensPic(pair[1], pair[0], l)
            if pic not in set(all_pics):
                all_pics.append(pic)
            else:
                skipped += 1

        if skipped:
            print(f'Skipped {skipped} already known images')

    for p in all_pics:
        html_text += f"<p><img class='result' src='{p.url}'><a href='{p.site}'><span>[{p.lang.upper()}]</span>{p.site}</a>\n"

    with open('report.html', 'w') as f:
        f.write(html_text)
