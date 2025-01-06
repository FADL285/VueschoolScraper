import requests
import os
from time import sleep
from src.utils import check_exists_by_css_selector
from src.browser import do_in_new_window
from selenium.webdriver.common.by import By
from decouple import config
from html2text import html2text

@do_in_new_window
def download_lesson_content(driver, lesson_url, lesson_index, course_title, choice):
    """
    Opens the lesson in a new tab, waits for the Vue.js app to render, and downloads the specified
    content (lessons, transcripts, repos, descriptions, or all) based on the user's choice.
    """
    lesson_title = driver.find_element(By.CSS_SELECTOR, "#app h1[title]").text
    print(f"Processing lesson: {lesson_title}")

    repo_elem_url = "Not Applicable"

    if choice in ["1", "3", "6"]:
        print(f"Downloading lesson video for {lesson_title}...")
        download_lesson(driver)

    if choice in ["2", "3", "6"]:
        print(f"Downloading transcript for {lesson_title}...")
        if not download_transcript(driver, lesson_title, lesson_index, course_title):
            print(f"Transcript not found, downloading subtitles for {lesson_title}...")
            download_subtitle(driver, lesson_title, lesson_index, course_title)

    if choice in ["4", "6"]:
        print(f"Downloading source code for {lesson_title}...")
        repo_elem_url = get_source_code_link(driver)

    if choice in ["5", "6"]:
        print(f"Downloading description for {lesson_title}...")
        download_description(driver, lesson_title, lesson_index, course_title)

    return repo_elem_url

def download_lesson(driver):
    try:
        download_elem = driver.find_element(By.LINK_TEXT, "HD")
        download_elem.click()
        print("Lesson video download initiated.")
    except Exception as e:
        print(f"Failed to download the lesson: {e}")

def download_transcript(driver, lesson_title, lesson_index, course_title):
    transcript_button_css = 'a[title^="Download the transcript"]'
    if check_exists_by_css_selector(driver, transcript_button_css):
        transcript_elem = driver.find_element(By.CSS_SELECTOR, transcript_button_css)
        transcript_elem.click()
        print(f"Transcript download initiated for {lesson_title}.")

        # Wait for the download to complete and rename the file
        download_path = config("DOWNLOAD_PATH")
        file_name = (
            f"Vue School - {course_title} - {lesson_index} {lesson_title} - HD.vtt"
            .replace("?", "_").replace("/", "_").replace("*", "_")
        )
        
        # Assuming the downloaded file is the latest file in the download directory
        sleep(5)  # Wait for the download to complete
        files = sorted(
            [f for f in os.listdir(download_path) if f.endswith(".vtt")],
            key=lambda x: os.path.getctime(os.path.join(download_path, x)),
            reverse=True
        )
        if files:
            latest_file = os.path.join(download_path, files[0])
            os.rename(latest_file, os.path.join(download_path, file_name))
            print(f"Downloaded Transcript for {lesson_title}.")
            return True
        else:
            print(f"Failed to find the downloaded transcript for {lesson_title}.")
            return False
    return False

def download_subtitle(driver, lesson_name, lesson_index, course_title):
    iframe_elem = driver.find_element(By.CSS_SELECTOR, ".video-player-wrapper iframe")
    driver.switch_to.frame(iframe_elem)

    if not check_exists_by_css_selector(driver, '.vp-video-wrapper video track[srclang="en-US"]'):
        return

    subtitle_elem = driver.find_element(By.CSS_SELECTOR, '.vp-video-wrapper video track[srclang="en-US"]')
    subtitle_link = str(subtitle_elem.get_attribute("src"))

    download_path = config("DOWNLOAD_PATH")
    file = requests.get(subtitle_link)
    file_name = (
        f"Vue School - {course_title} - {lesson_index} {lesson_name} - HD.vtt"
        .replace("?", "_").replace("/", "_").replace("*", "_")
    )

    with open(f"{download_path}/{file_name}", "wb") as f:
        f.write(file.content)

def get_source_code_link(driver):
    source_code_css = 'a[title^="Download the source code"]'
    if check_exists_by_css_selector(driver, source_code_css):
        source_code_elem = driver.find_element(By.CSS_SELECTOR, source_code_css)
        return source_code_elem.get_attribute("href")
    else:
        return "Not Found"

def download_description(driver, lesson_title, lesson_index, course_title):
    description_css = "div[data-link-blank]"
    if check_exists_by_css_selector(driver, description_css):
        description_elem = driver.find_element(By.CSS_SELECTOR, description_css)
        description_html = description_elem.get_attribute("innerHTML")
        markdown_text = html2text(description_html)

        download_path = config("DOWNLOAD_PATH")
        file_name = (
            f"Vue School - {course_title} - {lesson_index} {lesson_title} - Description.md"
            .replace("?", "_").replace("/", "_").replace("*", "_")
        )

        with open(f"{download_path}/{file_name}", "w", encoding="utf-8") as f:
            f.write(markdown_text)

        print(f"Downloaded description as Markdown for {lesson_title}.")
    else:
        print(f"No description found for {lesson_title}.")
