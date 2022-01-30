# Setup

- Create a `.env` file
- Copy & paste to `.env` with the proper values < See `.env.example` >:

```bash
CHROMEDRIVER=[path to driver]
EMAIL=[your email]
PASSWORD=[youe password]
COURSE_URL=[The course you want to download]
DOWNLOAD_PATH=[path that you want to download on it]
```

- Install the dependencies: `pip install -r requirements.txt`
- Run the script: `python script.py`
- The output will be saved to a text file (`download_urls.txt`)
