import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

books_chapter_dict = {
    "Matt": 28,
    "Mark": 16,
    "Luke": 24,
    "John": 21,
    "Acts": 28,
    "Rom": 16,
    "1Cor": 16,
    "2Cor": 13,
    "Gal": 6,
    "Eph": 6,
    "Phil": 4,
    "Col": 4,
    "1Thess": 5,
    "2Thess": 3,
    "1Tim": 6,
    "2Tim": 4,
    "Titus": 3,
    "Phlm": 1,
    "Heb": 13,
    "Jas": 5,
    "1Pet": 5,
    "2Pet": 3,
    "1John": 5,
    "2John": 1,
    "3John": 1,
    "Jude": 1,
    "Rev": 22,
}
total_chapters = sum(
    books_chapter_dict.values()
)  # Total number of chapters to iterate over


# Initialize the DataFrame for later output
df = pd.DataFrame(columns=["book", "chapter", "verse", "text"])

# set options for webdriver and start it
chrome_options = Options()
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--headless=new")  # for Chrome >= 109
driver = webdriver.Chrome(options=chrome_options)
# get the initial website
driver.get("https://ntvmr.uni-muenster.de/de/ecm")

try:
    # Wait until iframes are loaded and find all the iframes
    WebDriverWait(driver, 1).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "iframe"))
    )

    # Switch to the iframe, as we know it is the first one on top we set [0]
    iframe = driver.find_elements(By.TAG_NAME, "iframe")[0]
    driver.switch_to.frame(iframe)

    with tqdm(total=total_chapters, desc="Processing Books and Chapters") as pbar:
        # iterate over books and chapters in the dict
        for book, chapters in books_chapter_dict.items():
            for chapter in range(1, chapters + 1):
                book_chapter = f"{book} {chapter}"  # Format the book name and chapter
                text_input = driver.find_element(
                    By.NAME, "verseRef"
                )  # find "verseRef" input field
                text_input.click()  # click into the field
                time.sleep(2)  # wait for the click to be recognized
                text_input.clear()  # clear the field
                text_input.send_keys(
                    book_chapter
                )  # Enter the desired text (it is sufficient to set book name and the chapter number, as all verses will be loaded)
                text_input.send_keys(Keys.ENTER)  # send the input
                time.sleep(2)  # Wait for the table to refresh its content
                table = driver.find_element(By.TAG_NAME, "table")  # Find the table
                rows = table.find_elements(
                    By.TAG_NAME, "tr"
                )  # Get all rows from the table

                # Loop through the rows and extract data (e.g., print each row's data)
                for row in rows:
                    columns = row.find_elements(
                        By.TAG_NAME, "td"
                    )  # Get all <td> elements in the row
                    if columns:  # Ensure there's data in the columns
                        data = [
                            column.text for column in columns
                        ]  # Extract text from each column
                        data_to_add = [book, chapter] + data
                        df.loc[len(df)] = data_to_add  # Append the row to the DataFrame
                pbar.update(1)  # Update the progress bar after each chapter

finally:
    # remove unnecessary rows
    df = df[df["verse"] != "*"]
    # Merge the first three columns into a new column
    df["nkv"] = df.iloc[:, :3].apply(lambda x: ".".join(x.astype(str)), axis=1)
    df = df.drop(df.columns[:3], axis=1)
    # convert text to lowercase
    df["text"] = df["text"].str.lower()
    df.to_csv(
        "ecm_verses.csv", encoding="utf-8", mode="w", index=False
    )  # write to file
    driver.quit()  # cleanup driver
