# Vueschool Scraper

## Setup

1. **Create a `.env` file**
   - Copy & paste the following into the `.env` file with the appropriate values. See `.env.example` for reference:

   ```bash
   CHROMEDRIVER=[path to your ChromeDriver executable]
   EMAIL=[your email]
   PASSWORD=[your password]
   COURSE_URL=[the course URL you want to download]
   DOWNLOAD_PATH=[the path where you want to save downloads]
   WAIT_TIME=[optional: the wait time between downloads, default is 8 seconds]
   ```

2. **Create and activate a virtual environment**:

   - Create a virtual environment (if you haven't already):

     ```bash
     python -m venv venv
     ```

   - **Windows**: Activate the virtual environment with:

     ```bash
     .\venv\Scripts\activate
     ```

   - **macOS/Linux**: Activate the virtual environment with:

     ```bash
     source venv/bin/activate
     ```

3. **Install dependencies**:
   - After activating the virtual environment, install the required packages by running:

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the script**:
   - Navigate to the project root directory and run the script using:

   ```bash
   python -m src.main
   ```

5. **Choose content to download**:
   - During execution, you will be prompted to select which content you want to download:
     - `1`: Lessons only
     - `2`: Lessons and Transcripts
     - `3`: Repos only
     - `4`: Description only
     - `5`: All content

6. **Check the output**:
   - The downloaded files (lessons, transcripts, descriptions, etc.) will be saved to the directory specified in the `DOWNLOAD_PATH` of your `.env` file.
   - If downloading repos, the URLs will be saved to a text file with the format `repo-[from lesson]-[to lesson].txt`.

---

## Project Structure

```bash
VueschoolScraper/
│
├── src/
│   ├── __init__.py
│   ├── auth.py            # Handles user login
│   ├── downloader.py      # Handles downloading lessons, transcripts, and source code
│   ├── utils.py           # Utility functions like handle_params, save, and choose_content
│   ├── browser.py         # Manages new window/tab handling
│   └── main.py            # Entry point of the program
│
├── requirements.txt       # Dependencies required for the project
├── .env                   # Configuration file for personal environment variables (not included in the repo)
├── .env.example           # Example configuration file
├── README.md              # Project documentation
└── venv/                  # Virtual environment (not included in the repo)
```

---

## Notes

- Ensure that ChromeDriver is installed and that its path is correctly specified in the `.env` file.
- The script opens each lesson in a new browser tab, downloads the requested content, and then closes the tab.
- You can adjust the wait time between downloading lessons by setting the `WAIT_TIME` variable in your `.env` file.
