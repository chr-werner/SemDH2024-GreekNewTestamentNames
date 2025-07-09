import unicodedata

import pandas as pd

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


# Function to replace na28 with en book names
def replace_na28_with_en(nkv_value):
    # Extract the book name part (before the period) and check if it's in the BOOK_INFO
    book_code = nkv_value.split(".")[0]
    # Find the corresponding English book name from the BOOK_INFO
    for key, value in BOOK_INFO.items():
        if value["na28"] == book_code:
            return nkv_value.replace(book_code, value["en"])
    return nkv_value


def str_remove_diacritics(s: str) -> str:
    """Normalize string by removing accents and converting to lower case.

    - unicodedata.normalize('NFKD', s): normalizes the input Unicode string s using NFKD normalization. Valid normalization forms are 'NFC', 'NFKC', 'NFD', and 'NFKD'.

    :param s: String to be normalized.
    :return:  normalized string
    """
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if unicodedata.category(c) != "Mn"
    )


# read raw scraped data
df = pd.read_csv(
    "na28_verses_raw.csv", encoding="utf-8", dtype={"nkv": "str", "text": "str"}
)
# cleanup and merge
df.dropna(subset=["text"], inplace=True)
df = df.groupby("nkv", as_index=False)["text"].agg(" ".join)
# Apply the function to the 'nkv' column of the dataframe
df["nkv"] = df["nkv"].apply(replace_na28_with_en)
# remove diacritics and set to lowercase
df["text"] = df["text"].apply(str_remove_diacritics).str.lower()
# write to file
df.to_csv("na28_verses.csv", encoding="utf-8", mode="w", index=False)
