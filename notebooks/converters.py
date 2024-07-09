import pandas as pd
import re
from constants import BOOK_INFO


def docID_to_ga(doc_id: int) -> str or None:
    """Convert a docID to a GA string

    :param doc_id: docID integer value
    :return: GA string or NONE
    """
    # Get ga from row data
    doc_id_str = str(doc_id)

    if doc_id_str.startswith("1"):
        return "P" + doc_id_str[1:].lstrip("0")
    elif doc_id_str.startswith("2"):
        return "0" + doc_id_str[1:].lstrip("0")
    elif doc_id_str.startswith("3"):
        return doc_id_str[1:].lstrip("0")
    elif doc_id_str.startswith("4"):
        return "L" + doc_id_str[1:].lstrip("0")
    else:
        return None


def bkv_to_nkv(row: pd.Series) -> str or None:
    """Convert bkv values to nkv in a pandas dataframe row

    :param row: pandas dataframe row
    :return: nkv string or NONE
    """
    bkv = row["bkv"]
    pattern = r"B(\d{2})K(\d+)V(\d+)"

    try:
        match = re.match(pattern, bkv)
        book_num = match.group(1)
        kapitel = match.group(2)
        verse = match.group(3)

        book_abb_en = BOOK_INFO[str(book_num)]["en"]

        return f"{book_abb_en}.{kapitel}.{verse}" if book_abb_en else None
    except:
        return None


def string_to_list(value):
    """Splits an input into a list if input is a comma seperated string

    :param value:
    :return:
    """
    if isinstance(value, str):
        alt_set = set(value.split(","))
        return list(alt_set)
    else:
        return value  # If not a string, return the original value
