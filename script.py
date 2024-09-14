#! venv/bin/python
import requests

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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


def save(filename, repos_urls, lesson_from, lesson_to):
    download_path = config("DOWNLOAD_PATH")
    range_filename = (
        f"{filename}-{lesson_from}-{lesson_to}.txt"  # Include the range in the filename
    )
    with open(f"{download_path}/{range_filename}", "w") as f:
        f.write("\n\n".join(repos_urls))
    print(f"Repository URLs saved to {range_filename}")


def handle_params(lessons_numbers):
    params = {"from": 1, "to": lessons_numbers}

    print(f"Done! Found {lessons_numbers} lessons.")
    decision = input("Do you want to select a range of lessons? [y, n] --> ")

    if decision.lower() in ["y", "yes"]:
        range_from = input(
            f"Download <From> lesson No.?  [1-{lessons_numbers}], 1 is the default  --> "
        )
        params["from"] = (
            int(range_from)
            if range_from.isnumeric() and 0 < int(range_from) <= lessons_numbers
            else 1
        )

        range_to = input(
            f"Download <To> lesson No.?  [1-{lessons_numbers}], {lessons_numbers} is the default  --> "
        )
        params["to"] = (
            int(range_to)
            if range_to.isnumeric() and 0 < int(range_to) <= lessons_numbers
            else lessons_numbers
        )

    return params


def do_in_new_window(func):
    @wraps(func)
    def wrapper(driver, lesson_url, *args, **kwargs):
        # Open a new tab
        driver.switch_to.new_window('tab')

        # Navigate to the lesson URL in the new tab
        driver.get(lesson_url)

        # Wait for the Vue.js app to fully load
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#app h1[title]"))
            )
        except:
            print("Failed to load the lesson page in the new window.")
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            return "Page not loaded"

        # Execute the wrapped function while in the new tab
        res = func(driver, lesson_url, *args, **kwargs)

        # Close the tab and switch back to the main window
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        return res

    return wrapper


def download_lesson(driver):
    """
    Downloads the lesson video by clicking the 'HD' link. This function assumes that the
    driver is already on the lesson page and the page is fully loaded.
    """
    # Click on the "HD" button to download the lesson video
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
        transcript_url = transcript_elem.get_attribute("href")

        try:
            response = requests.get(transcript_url)
            if response.status_code == 200:  # Ensure the request is successful
                download_path = config("DOWNLOAD_PATH")
                file_name = (
                    f"Vue School - {course_title} - {lesson_index} {lesson_title} - HD.vtt"
                    .replace("?", "_").replace("/", "_").replace("*", "_")
                )

                with open(f"{download_path}/{file_name}", "wb") as f:
                    f.write(response.content)
                print(f"Downloaded Transcript for {lesson_title}.")
                return True
            else:
                print(f"Failed to download transcript for {lesson_title}. Status Code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error downloading transcript: {e}")
            return False
    return False



def download_subtitle(driver, lesson_name, lesson_index, course_title):
    iframe_elem = driver.find_element(By.CSS_SELECTOR, ".video-player-wrapper iframe")
    driver.switch_to.frame(iframe_elem)

    if not check_exists_by_css_selector(
        driver, '.vp-video-wrapper video track[srclang="en-US"]'
    ):
        return

    subtitle_elem = driver.find_element(
        By.CSS_SELECTOR, '.vp-video-wrapper video track[srclang="en-US"]'
    )

    subtitle_link = str(subtitle_elem.get_attribute("src"))

    download_path = config("DOWNLOAD_PATH")
    file = requests.get(subtitle_link)
    file_name = (
        f"Vue School - {course_title} - {lesson_index} {lesson_name} - HD.vtt".replace(
            "?", "_"
        )
        .replace("/", "_")
        .replace("*", "_")
    )

    with open(f"{download_path}/{file_name}", "wb") as f:
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
    description_css = "div[data-link-blank]"
    if check_exists_by_css_selector(driver, description_css):
        description_elem = driver.find_element(By.CSS_SELECTOR, description_css)
        description_html = description_elem.get_attribute("innerHTML")

        # Convert HTML to Markdown using html2text
        try:
            markdown_text = html2text(description_html)

            # Save the description content as a Markdown (.md) file
            download_path = config("DOWNLOAD_PATH")
            file_name = (
                f"Vue School - {course_title} - {lesson_index} {lesson_title} - Description.md"
                .replace("?", "_").replace("/", "_").replace("*", "_")
            )

            with open(f"{download_path}/{file_name}", "w", encoding="utf-8") as f:
                f.write(markdown_text)

            print(f"Downloaded description as Markdown for {lesson_title}.")
        except Exception as e:
            print(f"Failed to download description for {lesson_title}: {e}")
    else:
        print(f"No description found for {lesson_title}.")


@do_in_new_window
def download_lesson_content(driver, lesson_url, lesson_index, course_title, choice):
    """
    Opens the lesson in a new tab, waits for the Vue.js app to render, and downloads the specified
    content (lessons, transcripts, repos, descriptions, or all) based on the user's choice.
    """
    # Lesson title is retrieved after the page is loaded
    lesson_title = driver.find_element(By.CSS_SELECTOR, "#app h1[title]").text

    print(f"Processing lesson: {lesson_title}")

    # Initialize a default repo_elem_url
    repo_elem_url = "Not Applicable"

    # Based on the choice, download the relevant content
    if choice in ["1", "2", "5"]:  # If Lessons, Lessons and Transcripts, or All
        print(f"Downloading lesson video for {lesson_title}...")
        download_lesson(driver)  # Call the refactored download_lesson function

        if choice == "2" or choice == "5":  # If Transcripts or All
            print(f"Downloading transcript for {lesson_title}...")
            if not download_transcript(driver, lesson_title):
                print(f"Transcript not found, downloading subtitles for {lesson_title}...")
                download_subtitle(driver, lesson_title, lesson_index, course_title)

    if choice == "3" or choice == "5":  # If Repos or All
        print(f"Downloading source code for {lesson_title}...")
        repo_elem_url = get_source_code_link(driver)

    if choice == "4" or choice == "5":  # If Description or All
        print(f"Downloading description for {lesson_title}...")
        download_description(driver, lesson_title, lesson_index, course_title)

    # Return the repo URL if applicable or "Not Applicable" otherwise
    return repo_elem_url



def get_course_info(driver, course):
    course_info = {}
    driver.get(course)

    try:
        lessons = driver.find_elements(By.CLASS_NAME, "title")
        if not lessons:
            print("No lessons found.")
        course_info["lessons"] = [lesson.get_attribute("href") for lesson in lessons]
        course_info["title"] = driver.find_element(By.CSS_SELECTOR, "#header h1[title]").text
    except NoSuchElementException as e:
        print(f"Error retrieving course info: {e}")
        course_info["lessons"] = []
        course_info["title"] = "Unknown Title"

    return course_info



def login(driver):
    driver.get("https://vueschool.io/login/")
    
    # Find and enter the email
    email_elem = driver.find_element(By.XPATH, '//input[@placeholder="elon@musk.io"]')
    email = config("EMAIL")
    email_elem.send_keys(email)

    # Find and enter the password
    password_elem = driver.find_element(By.XPATH, '//input[@placeholder="Your super secret password"]')
    password = config("PASSWORD")
    password_elem.send_keys(password)
    password_elem.send_keys(Keys.RETURN)

    # Wait until the <a href="/profile"> is located, indicating successful login
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '//a[@href="/profile"]'))
        )
        print("Logged in successfully.")
    except Exception as e:
        print(f"Login failed: {e}")



def choose_content():
    while True:
        print("Which content do you want to download?")
        print("1. Lessons only")
        print("2. Lessons and Transcripts")
        print("3. Repos only")
        print("4. Description only")
        print("5. All content")

        choice = input("Enter the number corresponding to your choice (1-5): ")

        if choice in ["1", "2", "3", "4", "5"]:
            return choice
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")


def main():
    try:
        print("Initiating a driver...")

        driver_path = config("CHROMEDRIVER")
        download_path = config("DOWNLOAD_PATH")

        service = Service(driver_path)
        chrome_options = webdriver.ChromeOptions()
        prefs = {"download.default_directory": download_path}
        chrome_options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Done!")

        # Login
        print("Logging in...")
        login(driver)
        print("Done!")

        # Get the lessons
        print("Getting the lessons...")
        course = config("COURSE_URL")

        course_info = get_course_info(driver, course)
        lessons = course_info["lessons"]
        course_title = course_info["title"].replace("?", "").replace(":", "")

        if not lessons:
            print("No lessons found. Exiting.")
            return

        # Get lesson range from handle_params
        download_range = handle_params(len(lessons))
        lessons = lessons[(download_range["from"] - 1): download_range["to"]]

        # Ask the user which content to download
        choice = choose_content()

        # Initialize an empty list to collect repo URLs
        source_code_urls = []

        wait_time = int(config("WAIT_TIME", default=8))  # Use default value of 8 seconds if not configured

        # Start downloading based on the user's choice
        lesson_index = download_range["from"]
        for lesson_url in lessons:
            print(f"Downloading lesson No. {lesson_index}...")

            # Download the content based on user's choice
            repo_url = download_lesson_content(
                driver, lesson_url, lesson_index, course_title, choice
            )

            if choice == "3" or choice == "5":  # Repos only or All
                if repo_url != "Not Applicable":
                    source_code_urls.append(repo_url)

            if lesson_index % 2 == 0:
                sleep(wait_time)

            lesson_index += 1

        # If the user chose to download repos (or all content), save the repo URLs
        if choice == "3" or choice == "5":
            save("repo", source_code_urls, download_range["from"], download_range["to"])

        print("Done! Check Downloads in browser driver.")
        input("Enter key to close:) -> ")

    except Exception as e:
        print(f"An error occurred: {e}")



if __name__ == "__main__":
    main()
