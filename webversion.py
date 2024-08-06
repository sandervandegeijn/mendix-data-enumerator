from shared import *
import streamlit as st
from playwright.sync_api import sync_playwright, Playwright
import pandas as pd
import re
import os
import requests
import json

st.set_page_config(page_title="Mendix data enumerator", page_icon="🌐", layout="wide", initial_sidebar_state="auto")
st.title("Mendix data enumerator")

with st.form(key='url_form'):
    url = st.text_input("Enter URL:", value="https://application.mendixcloud.com/").strip()
    submit_button = st.form_submit_button(label='Start check')

    with sync_playwright() as playwright:

        if submit_button:
            st.write("Checking URL")
            if validate_url(url):
                st.success("The URL is valid! Let's start the check")
                st.write("Trying to get table list (this will take a few seconds - be patient)")
                
                st.header("Database table list")
                chromium = playwright.chromium
                browser = chromium.launch()
                page = browser.new_page()
                page.goto(url)
                page.wait_for_timeout(2000)
                try:
                    database_tables = get_database_tables(page)
                    st.dataframe(database_tables)

                    st.header("Contents of database tables")
                    st.write("Displaying first 10 records all tables with accessible data")

                    for index, row in database_tables.iterrows():
                        try:
                            database_table_name = row["Database tables"]
                            data = get_dataframe_for_table(page, database_table_name)
                            
                            if data is not None and len(data) != 0:
                                st.subheader(f"{database_table_name}:")
                                if "FileID" in data.columns:
                                    data["Download"] = data["FileID"].apply(lambda fileID: add_download_column(fileID, database_table_name, url, page))
                                    cols = data.columns.tolist()
                                    cols.insert(0, cols.pop(cols.index("Download")))
                                    data = data[cols]
                                st.dataframe(data)
                        except Exception as e:
                            st.error(f"Could not fetch data for table {database_table_name}")
                except:
                    st.error("Site does not expose data!")
            else:
                st.error("The URL is not valid. Please enter a correct URL starting with http or https.")