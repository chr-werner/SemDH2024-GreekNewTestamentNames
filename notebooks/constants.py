# Define a dictionary for book information
BOOK_INFO = {
    "01": {"de": "Matt", "en": "Matt", "na28": "MAT"},
    "02": {"de": "Mark", "en": "Mark", "na28": "MRK"},
    "03": {"de": "Luk", "en": "Luke", "na28": "LUK"},
    "04": {"de": "Joh", "en": "John", "na28": "JHN"},
    "05": {"de": "Apg", "en": "Acts", "na28": "ACT"},
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

# DATA_PATH = "/mnt/dev/nvme0n1/werchr/nt-data"     # when running on the server without the DevContainer
DATA_PATH = "../data/"  # When running in the DevContainer

# paths for temporary data (during parsing, name search, etc.), output path for processed data and publication
TMP_PATH = DATA_PATH + "tmp/"
PUB_PATH = DATA_PATH + "publication/"
