from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from decouple import config

def login(driver):
    driver.get("https://vueschool.io/login/")
    
    
    # Find and enter the email
    try:
        email_elem = driver.find_element(By.XPATH, '//input[@placeholder="guybrush@threepwood.com"]')
    except NoSuchElementException:
        try:
            email_elem = driver.find_element(By.XPATH, '//input[@tabindex="1"]')
        except NoSuchElementException:
            raise Exception("Email input not found")
    
    email = config("EMAIL")
    email_elem.send_keys(email)
    
    # Find and enter the password
    try:
        password_elem = driver.find_element(By.XPATH, '//input[@placeholder="Your super secret password"]')
    except NoSuchElementException:
        try:
            password_elem = driver.find_element(By.XPATH, '//input[@tabindex="2"]')
        except NoSuchElementException:
            raise Exception("Password input not found")
    
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
