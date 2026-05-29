import io
import json
import streamlit as st
from PIL import Image
from streamlit_cropper import st_cropper

from lingolens import *

def main():
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
    # proxies = await get_proxies()
    # selected_proxies = st.multiselect(
    #     'Choose proxies to use',
    #     proxies,
    #     [],
    # )  

    st.markdown('If you have search results distorted by the presence of some object, try to remove it through with [Cleanup.pictures](https://cleanup.pictures/) and use the processed image.')

    uploaded_file = st.file_uploader("Choose an image file to search")
    if uploaded_file is not None:
        original_bytes = uploaded_file.getvalue()
        original_image = Image.open(io.BytesIO(original_bytes)).convert('RGB')

        crop_mode = st.toggle('Select a region of the image to search', value=False)

        if crop_mode:
            st.write('Drag the corners of the box, then **double-click inside the box** to apply the crop:')
            saved_coords = st.session_state.get('crop_coords')
            saved_image_id = st.session_state.get('crop_image_id')
            current_image_id = (uploaded_file.name, uploaded_file.size)
            if saved_image_id != current_image_id:
                saved_coords = None
                st.session_state['crop_image_id'] = current_image_id

            cropped_image, box = st_cropper(
                original_image,
                realtime_update=False,
                box_color='#FF4B4B',
                aspect_ratio=None,
                return_type='both',
                key='lens_cropper',
                default_coords=saved_coords,
            )
            st.session_state['crop_coords'] = (
                box['left'],
                box['left'] + box['width'],
                box['top'],
                box['top'] + box['height'],
            )
            st.image(cropped_image, caption='Selected area (after double-click)', width=300)
            buf = io.BytesIO()
            cropped_image.save(buf, format='JPEG', quality=92)
            file_content = buf.getvalue()
            crop_name = f'{uploaded_file.name}_crop.jpg'
        else:
            st.image(original_image, caption=uploaded_file.name, width=500)
            file_content = original_bytes
            crop_name = uploaded_file.name

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
            with st.status('Searching with Google Lens...', expanded=True) as status:
                def on_lang(stat):
                    st.write(
                        f'**{stat.lang.upper()}**: {stat.total} total on page, '
                        f'{stat.new} new (rest were already seen via earlier langs)'
                    )

                result = search_and_generate_report(
                    crop_name, file_content, langs, on_lang=on_lang
                )
                status.update(
                    label=f'Done — {result.results_count} unique results',
                    state='complete',
                )

            if not result.results_count:
                st.markdown('No results, probable issues with Google captcha, try to run tool [locally](https://github.com/OSINT-mindset/lingolens#usage), switch off VPN or just check Google Images in browser incognito mode.')
            else:
                st.download_button(
                    f'Download report ({result.results_count} results)',
                    data=result.report_html,
                    mime='text/html',
                    file_name=file_name,
                )

                st.subheader(f'Results ({result.results_count})')
                cols = st.columns(3)
                for i, (img_url, ref_url, lang) in enumerate(result.image_data):
                    with cols[i % 3]:
                        st.image(img_url, use_column_width=True)
                        st.caption(f'**[{lang.upper()}]** [{ref_url}]({ref_url})')

                preview_uri = get_base64_image_uri(crop_name, file_content)
                st.markdown(
                    f'<img src="{preview_uri}" '
                    'style="position: fixed; bottom: 20px; right: 20px; '
                    'max-width: 200px; max-height: 200px; '
                    'border: 2px solid red; border-radius: 4px; '
                    'z-index: 9999; box-shadow: 0 2px 8px rgba(0,0,0,0.3); '
                    'background: #fff;">',
                    unsafe_allow_html=True,
                )

        if st.button(f'TEST OSINT #64', type="primary"):
            result = search_and_generate_report(crop_name, file_content, langs)

            if not result.report_html:
                st.markdown('BLOCK')
            elif 'pixels.com' in result.report_html:
                st.markdown('FOUND!!!')
            elif 'fineartamerica.com' in result.report_html:
                st.markdown('Fine, at least fineartamerica...')
            else:
                st.markdown('No result... :(')



if __name__ == "__main__":
    main()
