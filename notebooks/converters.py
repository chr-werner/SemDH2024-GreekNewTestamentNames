import pandas as pd
import re
from constants import BOOK_INFO
from TEIFile import TEIFile


def ga_to_docID(row: pd.Series) -> int:
    """Convert the GA string corresponding docID for a given row of a pandas dataframe

    :param row: pandas dataframe row
    :return: docID integer
    """
    # Get ga from row data
    ga = row["ga"]

    if not re.match(r"^[PL0-9]$", ga[0]):
        raise AttributeError

    # Compile the regular expression pattern
    pattern = re.compile(r"([0-9]\d*)")

    # Remove non-digits from ga
    ga_digits = re.search(pattern, ga).group()

    if ga[0] == "P":
        docID = 10000 + int(ga_digits)
    elif ga[0] == "0":
        docID = 20000 + int(ga_digits)
    elif ga[0].isdigit():
        docID = 30000 + int(ga_digits)
    elif ga[0] == "L":
        docID = 40000 + int(ga_digits)
    else:
        raise ValueError(
            f"Invalid input: cannot determine document ID for the given input. {ga},{ga_digits}"
        )

    if len(ga_digits) > 4 or len(str(docID)) != 5 or docID > 49999:
        raise ValueError

    return docID


def docID_to_ga(doc_id: int) -> str | None:
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


def bkv_to_nkv(row: pd.Series) -> str | None:
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


def tei_to_verses_dict(tei: TEIFile, source: str) -> list[dict]:
    """Extract verses from TEI file

    :param tei: TEI data
    :param source: verses source
    :return: list of dictionaries with verses data
    """
    entries_list = []
    verses = tei.verses
    manuscript = tei.manuscript

    # Remove entries where text is empty
    verses = [verse for verse in verses if verse.text.strip() != ""]

    for verse in verses:
        entries_list.append(
            {
                "docID": manuscript.docID,
                "ga": manuscript.ga,
                "bkv": verse.bkv,
                "text": verse.text,
                "marks": verse.marks,
                "publisher": verse.publisher,
                "source": source,
            }
        )
    return entries_list


def tei_to_manuscript_dict(tei: TEIFile, source: str) -> dict:
    """Extract manuscript data from TEI file

    :param tei: TEI data
    :param source: manuscript source
    :return: dictionary with manuscript data
    """
    manuscript = {
        "docID": tei.manuscript.docID,
        "ga": tei.manuscript.ga,
        "label": tei.manuscript.label,
        "source": source,
        # "sources": tei.manuscript.sources,
    }

    return manuscript
