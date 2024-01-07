import json
import streamlit as st

from lingolens import *

if __name__ == '__main__':
    all_languages = json.load(open('languages.json'))
    language_names = list(all_languages.keys())
    selected_lang_names = st.multiselect(
        'Choose languages to filter results',
        language_names,
        ['English', 'Polish', 'Korean'],
    )

    all_countries = json.load(open('countries.json'))
    countries_names = list(all_countries.keys())
    selected_country_names = st.multiselect(
        'Choose countries to search',
        countries_names,
        [],
    )

    uploaded_file = st.file_uploader("Choose an image file to search")
    if uploaded_file is not None:
        file_content = uploaded_file.read()
        st.image(uploaded_file, caption=uploaded_file.name, width=500)

        langs = []
        if not selected_country_names:
            selected_country_names = [""]

        for n in selected_lang_names:
            for c in selected_country_names:
                lang = all_languages[n]
                country = all_countries[c]
    
                if not country:
                    langs.append(lang)
                else:
                    langs.append(f'{lang}-{country.upper()}')

        langs = list(set(langs))
        st.write(f'A search will be conducted with the following language-country combinations: {", ".join(langs)}')

        file_name = f'{uploaded_file.name}_lens_report_{"_".join(langs)}.html'

        if st.button(f'Search in Google Lens with selected languages', type="primary"):
            report_html = main(uploaded_file.name, file_content, langs)

            with open(file_name, 'w', encoding='utf-8') as file:
                file.write(report_html)

            with open(file_name) as f:
               st.download_button('Download report', f, mime='text/html', file_name=file_name)
