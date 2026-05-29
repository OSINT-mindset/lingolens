#!/usr/bin/env python3
import atexit
import json
import os
import sys
from base64 import b64encode
from collections import namedtuple
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth


SearchResult = namedtuple(
    'SearchResult',
    ['report_html', 'results_count', 'image_data', 'lang_stats'],
)
LangStat = namedtuple('LangStat', ['lang', 'total', 'new'])


LENS_PROFILE_DIR = os.environ.get(
    'LINGOLENS_PROFILE_DIR', os.path.expanduser('~/.lingolens-profile')
)
LENS_HEADLESS = os.environ.get('LINGOLENS_HEADLESS', '1') == '1'
LENS_USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/124.0.0.0 Safari/537.36'
)

_LENS_STATE = {'stealth_cm': None, 'pw': None, 'ctx': None, 'locale': None}


def _clear_stale_chromium_lock(profile_dir):
    for name in ('SingletonLock', 'SingletonCookie', 'SingletonSocket'):
        path = os.path.join(profile_dir, name)
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
        except OSError:
            pass


def _mark_profile_exited_cleanly(profile_dir):
    """Suppress Chrome's "profile didn't exit cleanly" modal by patching prefs."""
    prefs_path = os.path.join(profile_dir, 'Default', 'Preferences')
    if not os.path.exists(prefs_path):
        return
    try:
        with open(prefs_path) as f:
            prefs = json.load(f)
    except (OSError, json.JSONDecodeError):
        return
    profile = prefs.setdefault('profile', {})
    if profile.get('exit_type') == 'Normal' and profile.get('exited_cleanly') is True:
        return
    profile['exit_type'] = 'Normal'
    profile['exited_cleanly'] = True
    try:
        with open(prefs_path, 'w') as f:
            json.dump(prefs, f)
    except OSError:
        pass


def _open_lens_context(locale):
    _clear_stale_chromium_lock(LENS_PROFILE_DIR)
    _mark_profile_exited_cleanly(LENS_PROFILE_DIR)
    cm = Stealth().use_sync(sync_playwright())
    pw = cm.__enter__()
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=LENS_PROFILE_DIR,
        headless=LENS_HEADLESS,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-session-crashed-bubble',
            '--hide-crash-restore-bubble',
            '--no-first-run',
        ],
        user_agent=LENS_USER_AGENT,
        locale=locale,
        viewport={'width': 1280, 'height': 900},
    )
    _LENS_STATE.update(stealth_cm=cm, pw=pw, ctx=ctx, locale=locale)
    return ctx


def _ensure_lens_context(locale):
    if _LENS_STATE['ctx'] is None or _LENS_STATE['locale'] != locale:
        close_lens_context()
        return _open_lens_context(locale)
    return _LENS_STATE['ctx']


def close_lens_context():
    ctx = _LENS_STATE.get('ctx')
    cm = _LENS_STATE.get('stealth_cm')
    if ctx is not None:
        try:
            ctx.close()
        except Exception:
            pass
    if cm is not None:
        try:
            cm.__exit__(None, None, None)
        except Exception:
            pass
    _LENS_STATE.update(stealth_cm=None, pw=None, ctx=None, locale=None)


atexit.register(close_lens_context)


def post_image_and_get_response_html(image_file_path, file_content, lang):
    ctx = _ensure_lens_context(lang)
    page = ctx.new_page()
    try:
        page.goto(f'https://lens.google.com/?hl={lang}',
                  wait_until='domcontentloaded', timeout=30000)
        page.wait_for_selector('input[type="file"][name="encoded_image"]',
                               state='attached', timeout=15000)
        page.locator('input[type="file"][name="encoded_image"]').first.set_input_files({
            'name': os.path.basename(image_file_path) or 'upload.jpg',
            'mimeType': 'image/jpeg',
            'buffer': file_content,
        })
        try:
            page.wait_for_url('**/search**', timeout=30000)
        except Exception:
            pass

        if '/sorry/' in page.url:
            print('Captcha detected. Solve it once in the opened browser '
                  '(LINGOLENS_HEADLESS=0) — the persistent profile will keep cookies.')
            return None

        try:
            page.wait_for_selector('div.kb0PBd.cvP2Ce a[href]', timeout=20000)
        except Exception:
            pass
        page.wait_for_timeout(1500)

        return page.content()
    finally:
        page.close()


def extract_image_urls(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    cards = soup.select('div.kb0PBd.cvP2Ce')

    if not cards:
        print("Error: No result cards found. Lens DOM may have changed again.")
        return []

    image_urls = []
    seen_refs = set()
    for card in cards:
        a = card.find('a', href=True)
        img = card.find('img', class_='VeBrne')
        if not (a and img):
            continue
        img_ref_url = a['href']
        if img_ref_url in seen_refs:
            continue
        seen_refs.add(img_ref_url)
        img_url = img.get('src') or ''
        image_urls.append((img_url, img_ref_url))

    return image_urls


def filter_unique_images(image_urls, processed_urls, lang):
    unique_images = []
    for img_url, img_ref_url in image_urls:
        if img_ref_url not in processed_urls:
            processed_urls.add(img_ref_url)
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

def search_and_generate_report(image_file_path, file_content, langs, on_lang=None):
    print(f"Starting analysis for '{image_file_path}'...")
    print(f"Languages for analysis: {', '.join(langs)}")

    processed_urls = set()
    image_data = []
    lang_stats = []

    for lang in langs:
        html_content = post_image_and_get_response_html(image_file_path, file_content, lang)
        total = new = 0
        if html_content:
            image_urls = extract_image_urls(html_content)
            unique_images = filter_unique_images(image_urls, processed_urls, lang)
            image_data.extend(unique_images)
            total = len(image_urls)
            new = len(unique_images)
        stat = LangStat(lang=lang, total=total, new=new)
        lang_stats.append(stat)
        print(f"{lang.upper()}: {total} total on page, {new} new "
              "(others already seen via earlier langs)")
        if on_lang is not None:
            on_lang(stat)

    results_count = len(image_data)
    report_html = None

    if results_count:
        target_image_uri = get_base64_image_uri(image_file_path, file_content)
        report_html = generate_html_report(image_data, target_image_uri)
        print("Report generated.")
    else:
        print("No results, probable captcha issues or search error")

    return SearchResult(
        report_html=report_html,
        results_count=results_count,
        image_data=image_data,
        lang_stats=lang_stats,
    )


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: ./lingolens.py <image filename>')
        sys.exit(1)

    filename = sys.argv[1]
    file_content = load_file_from_disk(filename)

    langs = read_langs('langs.txt') or ['ru', 'en', 'pl']

    if not file_content:
        print(f"File not found: {filename}")
    else:
        result = search_and_generate_report(filename, file_content, langs)

        if result.report_html:
            with open('report.html', 'w', encoding='utf-8') as file:
                file.write(result.report_html)

    print("Script execution completed.")
