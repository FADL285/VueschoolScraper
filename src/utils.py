from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from decouple import config

def check_exists_by_css_selector(driver, css_selector):
    try:
        driver.find_element(By.CSS_SELECTOR, css_selector)
    except NoSuchElementException:
        return False
    return True

def save(filename, repos_urls, lesson_from, lesson_to):
    download_path = config("DOWNLOAD_PATH")
    range_filename = (
        f"{filename}-{lesson_from}-{lesson_to}.txt"
    )
    with open(f"{download_path}/{range_filename}", "w") as f:
        f.write("\n\n".join(repos_urls))
    print(f"Repository URLs saved to {range_filename}")

def handle_params(lessons_numbers):
    params = {"from": 1, "to": lessons_numbers}
    print(f"Done! Found {lessons_numbers} lessons.")
    decision = input("Do you want to select a range of lessons? [y, n] --> ")

    if decision.lower() in ["y", "yes"]:
        range_from = input(f"Download <From> lesson No.?  [1-{lessons_numbers}], 1 is the default  --> ")
        params["from"] = (
            int(range_from) if range_from.isnumeric() and 0 < int(range_from) <= lessons_numbers else 1
        )
        range_to = input(f"Download <To> lesson No.?  [1-{lessons_numbers}], {lessons_numbers} is the default  --> ")
        params["to"] = (
            int(range_to) if range_to.isnumeric() and 0 < int(range_to) <= lessons_numbers else lessons_numbers
        )

    return params

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
