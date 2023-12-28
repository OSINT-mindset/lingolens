from lingolens import *
import streamlit as st

if __name__ == '__main__':
    uploaded_file = st.file_uploader("Choose an image file to search")
    if uploaded_file is not None:
        file_content = uploaded_file.read()

        if st.button(f'Search!', type="primary"):
            report_html = main(uploaded_file.name, file_content)

            with open('report.html', 'w', encoding='utf-8') as file:
                file.write(report_html)

            with open('report.html') as f:
               st.download_button('Download report', f, mime='text/html', file_name='report.html')
