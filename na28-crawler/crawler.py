import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

# Define the BOOK_INFO dictionary
BOOK_INFO = {
    "01": {"de": "Matt", "en": "Matt", "na28": "MAT"},
    "02": {"de": "Mark", "en": "Mark", "na28": "MRK"},
    "03": {"de": "Luk", "en": "Luke", "na28": "LUK"},
    "04": {"de": "Joh", "en": "John", "na28": "JHN"},
    "05": {"de": "", "en": "Acts", "na28": "ACT"},
    "06": {"de": "", "en": "Rom", "na28": "ROM"},
    "07": {"de": "1.Kor", "en": "1Cor", "na28": "1CO"},
    "08": {"de": "2.Kor", "en": "2Cor", "na28": "2CO"},
    "09": {"de": "", "en": "Gal", "na28": "GAL"},
    "10": {"de": "", "en": "Eph", "na28": "EPH"},
    "11": {"de": "", "en": "Phil", "na28": "PHP"},
    "12": {"de": "Kol", "en": "Col", "na28": "COL"},
    "13": {"de": "", "en": "1Thess", "na28": "1TH"},
    "14": {"de": "", "en": "2Thess", "na28": "2TH"},
    "15": {"de": "1Tim", "en": "1Tim", "na28": "1TI"},
    "16": {"de": "", "en": "2Tim", "na28": "2TI"},
    "17": {"de": "", "en": "Titus", "na28": "TIT"},
    "18": {"de": "", "en": "Philem", "na28": "PHM"},
    "19": {"de": "", "en": "Heb", "na28": "HEB"},
    "20": {"de": "Jak", "en": "James", "na28": "JAS"},
    "21": {"de": "", "en": "1Pet", "na28": "1PE"},
    "22": {"de": "", "en": "2Pet", "na28": "2PE"},
    "23": {"de": "", "en": "1John", "na28": "1JN"},
    "24": {"de": "", "en": "2John", "na28": "2JN"},
    "25": {"de": "", "en": "3John", "na28": "3JN"},
    "26": {"de": "", "en": "Jude", "na28": "JUD"},
    "27": {"de": "", "en": "Rev", "na28": "REV"},
}

books_chapter_dict = {
    "MAT": 28,
    "MRK": 16,
    "LUK": 24,
    "JHN": 21,
    "ACT": 28,
    "ROM": 16,
    "1CO": 16,
    "2CO": 13,
    "GAL": 6,
    "EPH": 6,
    "PHP": 4,
    "COL": 4,
    "1TH": 5,
    "2TH": 3,
    "1TI": 6,
    "2TI": 4,
    "TIT": 3,
    "PHM": 1,
    "HEB": 13,
    "JAS": 5,
    "1PE": 5,
    "2PE": 3,
    "1JN": 5,
    "2JN": 1,
    "3JN": 1,
    "JUD": 1,
    "REV": 22,
}

# generate urls
base_url = "https://www.die-bibel.de/en/bible/NA28/"
urls = []

for book, chapters in books_chapter_dict.items():
    for chapter in range(1, chapters + 1):
        urls.append(f"{base_url}{book}.{chapter}")

# Initialize the a list of dataframe for later output
books = []

# set options for webdriver and start it
chrome_options = Options()
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--headless=new")  # for Chrome >= 109
driver = webdriver.Chrome(options=chrome_options)

for url in tqdm(urls, desc="Processing URLs"):
    # Initialize the DataFrame for later output
    nkvs = []
    texts = []
    # get the initial website
    driver.get(url)

    try:
        # Define the XPath or CSS selector for the target <div> element
        target_xpath = "//div[@class='!font-greek' and @style='direction: ltr;']"

        # Wait until the element is visible
        div_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, target_xpath))
        )

        # Find all <span> elements with observevisibility=""
        span_elements = div_element.find_elements(
            By.XPATH, ".//span[@observevisibility='']"
        )

        # Iterate over the <span> elements and get their text and data-verse-org-id attribute
        for span in span_elements:
            span_text = span.text  # Get the visible text inside the <span>
            verse_org_id = span.get_attribute(
                "data-verse-org-id"
            )  # Get the data-verse-org-id attribute
            # append data to dataframe
            nkvs.append(verse_org_id)
            texts.append(span_text)

    except Exception as e:
        print("Error:", e)

    # Create a DataFrame
    df = pd.DataFrame({"nkv": nkvs, "text": texts})
    books.append(df)

driver.quit()  # cleanup driver

na28_dataframe = pd.concat(books, ignore_index=True)

na28_dataframe.to_csv(
    "na28_verses_raw.csv", encoding="utf-8", mode="w", index=False
)  # write to file
