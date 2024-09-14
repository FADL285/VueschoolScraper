#! venv/bin/python
import requests

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from functools import wraps
from decouple import config
from time import sleep
from html2text import html2text


def check_exists_by_css_selector(driver, css_selector):
    try:
        driver.find_element(By.CSS_SELECTOR, css_selector)
    except NoSuchElementException:
        return False
    return True


def save(filename, repos_urls):
    download_path = config("DOWNLOAD_PATH")
    with open(f"{download_path}/{filename}", "w") as f:
        f.write("\n\n".join(repos_urls))


def handle_params(lessons_numbers):
    params = {'from': 1, 'to': lessons_numbers}

    print(f"Done! Found {lessons_numbers} lessons.")
    decision = input("Do you want to select a range of lessons? [y, n] --> ")

    if decision.lower() == 'y' or decision.lower() == 'yes':
        range_from = input(f"Download <From> lesson No.?  [1-{lessons_numbers}], 1 is the default  --> ")
        params['from'] = int(range_from) if range_from.isnumeric() and 0 < int(range_from) <= lessons_numbers else 1

        range_to = input(f"Download <To> lesson No.?  [1-{lessons_numbers}], {lessons_numbers} is the default  --> ")
        params['to'] = int(range_to) if range_to.isnumeric() and 0 < int(
            range_to) <= lessons_numbers else lessons_numbers

    return params


def do_in_new_window(func):
    @wraps(func)
    def wrapper(driver, page, lesson_number, course_title, *args, **kwargs):
        driver.switch_to.new_window()

        res = func(driver, page, lesson_number, course_title)

        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        return res

    return wrapper


@do_in_new_window
def download_lesson(driver, lesson_url, lesson_index, course_title):
    driver.get(lesson_url)

    # Get Lesson Title
    lesson_title = driver.find_element(By.CSS_SELECTOR, '#app h1[title]').text

    # Download lesson
    download_elem = driver.find_element(By.LINK_TEXT, "HD")
    download_elem.click()

    # Try downloading the transcript first, fall back to subtitles if not found
    if not download_transcript(driver, lesson_title):
        download_subtitle(driver, lesson_title, lesson_index, course_title)

    # Get Source Code Link using the new function
    repo_elem_url = get_source_code_link(driver)

    # Download the lesson description if available
    download_description(driver, lesson_title, lesson_index, course_title)

    return repo_elem_url


def download_transcript(driver, lesson_title, lesson_index, course_title):
    """
    Checks for the 'Download Transcript' button and clicks on it.
    If the button is not found, it falls back to download_subtitle.
    """
    # Check if the "Download Transcript" button exists
    transcript_button_css = 'a[title^="Download the transcript"]'
    if check_exists_by_css_selector(driver, transcript_button_css):
        transcript_elem = driver.find_element(By.CSS_SELECTOR, transcript_button_css)
        transcript_url = transcript_elem.get_attribute("href")
        
        # Download the transcript
        download_path = config("DOWNLOAD_PATH")
        file = requests.get(transcript_url)
        file_name = f"Vue School - {course_title} - {lesson_index} {lesson_title} - HD.vtt".replace('?', '_').replace('/', '_').replace('*', '_')

        with open(f'{download_path}/{file_name}', 'wb') as f:
            f.write(file.content)
        print(f"Downloaded Transcript for {lesson_title}.")
        return True  # Transcript successfully downloaded
    else:
        return False  # Transcript button not found


def download_subtitle(driver, lesson_name, lesson_index, course_title):
    iframe_elem = driver.find_element(By.CSS_SELECTOR, ".video-player-wrapper iframe")
    driver.switch_to.frame(iframe_elem)

    if not check_exists_by_css_selector(driver, '.vp-video-wrapper video track[srclang="en-US"]'):
        return

    subtitle_elem = driver.find_element(By.CSS_SELECTOR, '.vp-video-wrapper video track[srclang="en-US"]')

    subtitle_link = str(subtitle_elem.get_attribute("src"))

    download_path = config("DOWNLOAD_PATH")
    file = requests.get(subtitle_link)
    file_name = f"Vue School - {course_title} - {lesson_index} {lesson_name} - HD.vtt".replace('?', '_').replace('/', '_').replace('*', '_')

    with open(f'{download_path}/{file_name}', 'wb') as f:
        f.write(file.content)


def get_source_code_link(driver):
    """
    Tries to find the 'Download Source Code' button and returns the link to the source code.
    Returns "Not Found" if the button is not present.
    """
    source_code_css = 'a[title^="Download the source code"]'
    
    # Check if the "Download Source Code" button exists
    if check_exists_by_css_selector(driver, source_code_css):
        source_code_elem = driver.find_element(By.CSS_SELECTOR, source_code_css)
        source_code_url = source_code_elem.get_attribute("href")
        return source_code_url
    else:
        return "Not Found"


def download_description(driver, lesson_title, lesson_index, course_title):
    """
    Checks for the 'data-link-blank' div, extracts its readable content (converted to Markdown),
    and saves it to a .md file.
    """
    # Check if the description div exists
    description_css = 'div[data-link-blank]'
    if check_exists_by_css_selector(driver, description_css):
        description_elem = driver.find_element(By.CSS_SELECTOR, description_css)
        description_html = description_elem.get_attribute("innerHTML")  # Get the inner HTML content
        
        # Convert HTML to Markdown using html2text
        markdown_text = html2text(description_html)
        
        # Save the description content as a Markdown (.md) file
        download_path = config("DOWNLOAD_PATH")
        file_name = f"Vue School - {course_title} - {lesson_index} {lesson_title} - Description.md".replace('?', '_').replace('/', '_').replace('*', '_')
        
        with open(f'{download_path}/{file_name}', 'w', encoding='utf-8') as f:
            f.write(markdown_text)
        
        print(f"Downloaded description as Markdown for {lesson_title}.")
    else:
        print(f"No description found for {lesson_title}.")


def get_course_info(driver, course):
    course_info = {}
    driver.get(course)
    course_info["lessons"] = [lesson.get_attribute("href") for lesson in driver.find_elements(By.CLASS_NAME, 'title')]
    course_info["title"] = driver.find_element(By.CSS_SELECTOR, "#header h1[title]").text
    return course_info


def login(driver):
    driver.get("https://vueschool.io/login/")

    email_elem = driver.find_element(By.XPATH, '//input[@placeholder="elon@musk.io"]')
    email = config("EMAIL")
    email_elem.send_keys(email)

    password_elem = driver.find_element(By.XPATH, '//input[@placeholder="Your super secret password"]')
    password = config("PASSWORD")
    password_elem.send_keys(password)
    password_elem.send_keys(Keys.RETURN)

    # Wait a bit (will be some issue with authentication if we didn't wait)
    sleep(4)


def main():
    # Init
    print("Initiating a driver...")

    driver_path = config("CHROMEDRIVER")
    download_path = config("DOWNLOAD_PATH")

    service = Service(driver_path)
    chrome_options = webdriver.ChromeOptions()
    # Change Download Path
    prefs = {"download.default_directory": download_path}
    chrome_options.add_experimental_option("prefs", prefs)
    # chrome_options.add_argument("--headless")  # Headless
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("Done!")

    # Login
    print("Logging in...")
    login(driver)
    print("Done!")

    # Get lessons
    print("Getting the lessons...")
    course = config("COURSE_URL")
    print(f"Course URL from env: {course}")

    course_info = get_course_info(driver, course)
    lessons = course_info["lessons"]
    course_title = course_info["title"].replace('?', '').replace(':', '')

    download_range = handle_params(len(lessons))
    lessons = lessons[(download_range['from'] - 1):download_range['to']]

    # Get a download url for each lesson
    print("Starting download lessons...., please wait.")

    source_code_urls = []
    lesson_index = download_range['from']
    for lesson in lessons:
        print(f"Downloading lesson No. {lesson_index}...")
        repo_url = download_lesson(driver, lesson, lesson_index, course_title)
        source_code_urls.append(repo_url)

        if lesson_index % 2 == 0:
            sleep(8)

        lesson_index += 1

    save('repo.txt', source_code_urls)
    print("Done! check Downloads in browser driver.")
    input('Enter key to close:) -> ')


if __name__ == "__main__":
    main()
