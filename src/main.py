from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from time import sleep
from decouple import config

# Import your custom modules
from src.auth import login
from src.utils import handle_params, save, choose_content, get_course_info
from src.downloader import download_lesson_content

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
        print(f"Course URL: {course}")

        course_info = get_course_info(driver, course)
        lessons = course_info["lessons"]
        course_title = course_info["title"].replace("?", "").replace(":", "")
        print(f"Course Title: {course_title}")

        if not lessons:
            print("No lessons found. Exiting.")
            return

        # Get lesson range from handle_params
        download_range = handle_params(len(lessons))
        lessons = lessons[(download_range["from"] - 1): download_range["to"]]

        # Ask the user which content to download
        choice = choose_content()

        source_code_urls = []
        wait_time = int(config("WAIT_TIME", default=25))

        lesson_index = download_range["from"]
        for lesson_url in lessons:
            print(f"Downloading lesson No. {lesson_index}...")

            repo_url = download_lesson_content(
                driver, lesson_url, lesson_index, course_title, choice
            )

            if choice == "3" or choice == "5":
                if repo_url != "Not Applicable":
                    source_code_urls.append(repo_url)

            if lesson_index % 2 == 0:
                sleep(wait_time)
            else:
                sleep(wait_time / 2)

            lesson_index += 1

        if choice == "3" or choice == "5":
            save("repo", source_code_urls, download_range["from"], download_range["to"])

        print("Done! Check Downloads in browser driver.")
        input("Enter key to close:) -> ")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
