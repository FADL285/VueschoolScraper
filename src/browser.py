from functools import wraps
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

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
