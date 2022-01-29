#! venv/bin/python
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from functools import wraps
from decouple import config
from time import sleep

def save(filename, download_urls):
	with open(filename, "w") as f:
		f.write("\n".join(download_urls))

def do_in_new_window(func):
	@wraps(func)
	def wrapper(driver, page, *args, **kwargs):
		driver.switch_to.new_window()
		
		res = func(driver, page)

		driver.close()
		driver.switch_to.window(driver.window_handles[0])
		return res
	return wrapper

@do_in_new_window
def get_download_url(driver, lesson):
	driver.get(lesson)
	download_elem = driver.find_element(By.LINK_TEXT, "HD")
	download_url = str(download_elem.get_attribute("href"))
	
	return download_url

def get_lessons(driver, course):
	driver.get(course)
	lessons = [ lesson.get_attribute("href") for lesson in driver.find_elements(By.CLASS_NAME, 'title') ]
	return lessons

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
	sleep(5)

def main():

	# Init
	print("Initiating a headless driver...")
	driver_path = config("CHROMEDRIVER")

	service = Service(driver_path)
	options = webdriver.ChromeOptions()
	options.add_argument("--headless") # Headless
	driver = webdriver.Chrome(service=service, options=options)
	print("Done!")

	# Login
	print("Logging in...")
	login(driver)
	print("Done!")

	# Get lessons
	print("Getting the lessons...")
	course = config("COURSE_URL")
	lessons = get_lessons(driver, course)
	print(f"Done! Found {len(lessons)} lessons.")

	# Get a download url for each lesson
	print("Getting the download urls")
	download_urls = []
	for lesson in lessons:
		download_url = get_download_url(driver, lesson)

		download_urls.append(download_url)

		# Save
		save("download_urls.txt", download_urls)
		print(f"Found ({len(download_urls)}/{len(lessons)})", end="\r")

	print("Done! check 'download_urls.txt'")

if __name__ == "__main__":
	main()