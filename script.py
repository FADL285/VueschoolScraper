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

    # Download Subtitle
    download_subtitle(driver, lesson_title, lesson_index, course_title)

    # Get Source Code Link
    repo_elem_url = "Not Found"
    if check_exists_by_css_selector(driver, 'aside .locked-feature a[title^="Download the source code"]'):
        repo_elem = driver.find_element(By.CSS_SELECTOR, 'aside .locked-feature a[title^="Download the source code"]')
        repo_elem_url = str(repo_elem.get_attribute("href"))

    return repo_elem_url


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
