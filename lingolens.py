#!/usr/bin/env python3
import os
import sys
from time import time, sleep
from base64 import b64encode
from requests import post
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote, quote


def post_image_and_get_response_html(image_file_path, file_content, lang):
    headers = {
        'Cookie': 'NID=511=eoiYVbD3qecDKQrHrtT9_jFCqvrNnL-GSi7lPJANAlHOoYlZOhFjOhPvcc'
                  '-43ZSGmBx_L5D_Irknb8HJvUMo41sCh1i0homN3Taqg2z7mdjnu3AQe-PbpKAyKE4zW1'
                  '-N6niKTJAMkV6Jq4AWPwp6txH_c24gjt7fU3LWAfNIezA'
    }
    timestamp = int(time() * 1000)
    url = f'https://lens.google.com/v3/upload?hl={lang}&re=df&stcs={timestamp}&vpw=1500&vph=1500'

    files = {'encoded_image': (image_file_path, file_content, 'image/jpeg')}
    response = post(url, files=files)

    return response.text if response.status_code == 200 else None


def extract_image_urls(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    divs = soup.find_all('div', class_='Vd9M6')

    if not divs:
        print("Error: The expected content is not found on the page. This might be due to a change in the website's "
              "layout. Please report this issue for further assistance.")
        return []

    problematic_domains = ['yandex.com', 'yandex.ru', 'instagram.com', 'facebook.com', 'fbsbx.com', 'tiktok.com']

    image_urls = []
    for div in divs:
        action_url = div.get('data-action-url')
        if action_url:
            parsed_url = urlparse(action_url)
            query_params = parse_qs(parsed_url.query)
            img_url = unquote(query_params.get('imgurl', [None])[0])
            img_ref_url = unquote(query_params.get('imgrefurl', [None])[0])

            img_is_problematic = any([p in img_url for p in problematic_domains])
            if img_url.startswith('x-raw-image') or img_is_problematic:
                div_thumb = div.find(lambda tag:tag.name == "div" and 'data-thumbnail-url' in tag.attrs)
                img_url = div_thumb.get('data-thumbnail-url')

            image_urls.append((img_url, img_ref_url))

    return image_urls


def normalize_url(url):
    parsed_url = urlparse(url)
    url_path = os.path.dirname(parsed_url.path)
    normalized_path = quote(url_path)
    normalized_url = f'{parsed_url.scheme}://{parsed_url.netloc}{normalized_path}'
    return normalized_url


def filter_unique_images(image_urls, processed_urls, lang):
    unique_images = []
    for img_url, img_ref_url in image_urls:
        normalized_url = normalize_url(img_url)
        if normalized_url not in processed_urls:
            processed_urls.add(normalized_url)
            unique_images.append((img_url, img_ref_url, lang))
    return unique_images


def read_langs(file_path):
    if os.path.exists(file_path):
        with open(file_path) as file:
            return [line.strip() for line in file.readlines()]
    else:
        print(f"Language file not found: {file_path}")
        return None


def get_base64_image_uri(image_file_path, file_content):
    img_type = 'image/png' if image_file_path.endswith('.png') else 'image/jpeg'
    img_encoded = b64encode(file_content).decode()

    return f"data:{img_type};base64,{img_encoded}"


def generate_html_report(image_data, target_image_uri):
    print("Generating HTML report...")
    languages = set(lang for _, _, lang in image_data)
    css_style = """
        html{
            background-color: #d0d2d2;
        }
        body {
            margin-top: 30px;
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
            right: 20px;
            bottom: 20px;
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
        .result-item {
            display: inline-block;
        }
        select {
            position: absolute;
            padding: 10px;
            top: 5px;
            left: 5px;
        }
        """
    script = """
        <script>
        function filterByLanguage(lang) {
            document.querySelectorAll('.result-item').forEach(item => {
                item.style.display = item.getAttribute('data-lang') === lang || lang === 'all' ? 'inline-block' : 'none';
            });
        }
        </script>
        """
    html_content = f"""<html>
        <head>
            <meta charset='UTF-8'>
            <title>Results of Google Lens search</title>
            <style>{css_style}</style>
        </head>
        <body>
            <select onchange="filterByLanguage(this.value)">
                <option value="all">All Languages</option>
                {''.join(f'<option value="{lang}">{lang.upper()}</option>' for lang in languages)}
            </select>
            {script}
            <img class="target" src="{target_image_uri}">
        """
    for img_url, img_ref_url, lang in image_data:
        html_content += (f"<div class='result-item' data-lang='{lang}'><p>"
                         f"<a href='{img_url}'><img class='result' src='{img_url}' alt='Image'></a>"
                         f"<a href='{img_ref_url}'><span>[{lang.upper()}]</span> {img_ref_url}</a></p></div>")

    html_content += "</body></html>"
    return html_content


def load_file_from_disk(image_file_path):
    if not os.path.exists(image_file_path):
        return

    file_content = None

    with open(image_file_path, 'rb') as f:
        file_content = f.read()

    return file_content

def main(image_file_path, file_content, langs):
    print(f"Starting analysis for '{image_file_path}'...")
    sleep(1.5)
    print(f"Languages for analysis: {', '.join(langs)}")

    processed_urls = set()
    all_images = set()

    for lang in langs:
        html_content = post_image_and_get_response_html(image_file_path, file_content, lang)
        if html_content:
            image_urls = extract_image_urls(html_content)
            unique_images = filter_unique_images(image_urls, processed_urls, lang)
            all_images.update(unique_images)
            print(f"Found {len(unique_images)} results for {lang.upper()} language")

    target_image_uri = get_base64_image_uri(image_file_path, file_content)
    report_html = generate_html_report(all_images, target_image_uri)
    print("Report generated.")

    return report_html


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: ./lingolens.py <image filename>')
        sys.exit(1)

    filename = sys.argv[1]
    file_content = load_file_from_disk(filename)

    langs = read_langs('langs.txt') or ['ru', 'en', 'pl']

    if not file_content:
        print(f"File not found: {image_file_path}")
    else:
        report_html = main(filename, file_content, langs)

        with open('report.html', 'w', encoding='utf-8') as file:
            file.write(report_html)

    print("Script execution completed.")
