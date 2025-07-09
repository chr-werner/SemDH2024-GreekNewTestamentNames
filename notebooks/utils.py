import csv
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
from constants import BOOK_INFO
from TEIFile import TEIFile


def check_and_create_file(file_path):
    # Check if the file already exists
    if not os.path.exists(file_path):
        # Get the directory path
        dir_path = os.path.dirname(file_path)

        # Create the directory path if it does not exist
        check_and_create_directory(dir_path)

        # Create the file
        with open(file_path, "w") as file:
            file.write("")
            print(f"File created: {file_path}")


def check_and_create_directory(directory_path):
    # Create the directory path if it does not exist
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Directory created: {directory_path}")


def url_to_error_log(url: str, reason: str | None, error_log_file: str):
    """Print an error message to given log file

    :param url: Url string which produced an error
    :param reason: the error text
    :param error_log_file: path to log file
    :return:
    """
    check_and_create_file(error_log_file)

    with open(error_log_file, "a") as error_log:
        error_log.write(f"{url}; {reason}\n")


def fetch_and_format_xml(url: str, output_file: str, error_log_file: str):
    """Fetches an XML file from the given URL, formats it to be humanreadable and writes it to an output file

    :param url: URL to the XML
    :param output_file: Path to the output file
    :param error_log_file: Path to the log file
    :return:
    """
    check_and_create_file(error_log_file)

    try:
        response = requests.get(url)
        if response.status_code == 200 and "text/xml" in response.headers.get(
            "content-type", ""
        ):
            root = ET.fromstring(response.text)
            # Check for <error> tag with code attribute equal to 1
            if root.tag == "error":
                url_to_error_log(url, root.get("message"), error_log_file)
                return
            # format XML
            xml_string = format_xml(root)
            # Write the string to the output file without any formatting
            with open(output_file, "w") as f:
                f.write(xml_string)
        else:
            url_to_error_log(url, "no xml found", error_log_file)

    except Exception as e:
        url_to_error_log(url, str(e), error_log_file)


def format_xml(root: ET.Element) -> str:
    """Formatting an XML element to be a one line string

    :param root: XML root element
    :param output_file: fiel to write formatted XML to
    """
    # Convert the XML element tree to a string without formatting (removing newlines and spaces between tags)
    xml_string = (
        ET.tostring(root, encoding="utf-8", method="xml")
        .decode("utf-8")
        .replace("\n", "")
    )
    return re.sub(r"\s{2,}", "", xml_string)


def check_xml(file_path: str, parser) -> Optional[str]:
    """Check XML file validity

    :param file_path: path string to file to be checked
    :param parser: parser class
    :return: file path string or NONE
    """
    try:
        parser.parse(file_path)
        return file_path
    except:
        return None


def get_unique_error_data(error_data) -> dict:
    """TODO: this function should not be needed, but the parser throws same errors multiple times. You can test this with ntvmr/10001.xml"""
    errors = error_data["errors"]
    file = error_data["file"]
    # Use a set to track seen items
    seen = set()
    unique_errors = []
    for error in errors:
        # Convert dictionary to a frozenset of its items for hashability
        error_tuple = frozenset(error.items())
        if error_tuple not in seen:
            seen.add(error_tuple)
            unique_errors.append(error)
    return {"file": file, "errors": unique_errors}


def get_data_from_tei(
    tei_file_path: str,
    clear_only,
    verbose: bool = False,
    write_to_file: bool = False,
    trans_out_dir: str = "../data/parsed/trans",
    man_out_dir: str = "../data/parsed/man",
    nomsac_out_dir: str = "../data/parsed/nomsac",
    error_out_dir: str = "../data/parsed/errors",
) -> tuple | None:
    """Wrapper function to extract manuscript and verse data from TEI file

    :param nomsac_out_dir:
    :param man_out_dir:
    :param trans_out_dir:
    :param verbose:
    :param clear_only: set True to get GAP indicators for supplied and illegible text
    :param write_to_file: set True to write results to files
    :param tei_file_path: TEI file path
    :return: tupel with manuscript and verses data
    """
    tei = TEIFile(tei_file_path, clear_only, verbose)
    file_name = Path(tei_file_path).stem
    nomsac = tei.nomsac
    man_data = tei.get_manuscript_data()
    trans_data = tei.get_transcription_list()
    error_data = tei.get_error_data()

    if not write_to_file:
        return man_data, trans_data, nomsac
    else:
        with open(f"{man_out_dir}/{file_name}.csv", "w", newline="") as file1:
            w = csv.DictWriter(file1, fieldnames=man_data.keys())
            w.writeheader()
            w.writerow(man_data)
        with open(f"{trans_out_dir}/{file_name}.csv", "w", newline="") as file2:
            w = csv.DictWriter(file2, fieldnames=trans_data[0].keys())
            w.writeheader()
            w.writerows(trans_data)
        if error_data:
            error_data = get_unique_error_data(error_data)
            with open(
                f"{error_out_dir}/{file_name}.json", "w", encoding="utf8"
            ) as file3:
                json.dump(error_data, file3, ensure_ascii=False)
        if nomsac:
            with open(f"{nomsac_out_dir}/{file_name}.csv", "w", newline="") as file3:
                w = csv.DictWriter(file3, fieldnames=nomsac[0].keys())
                w.writeheader()
                w.writerows(nomsac)


def bkv_nkv_from_verse_id(row: pd.Series, verse_id_col: str = "verse") -> pd.Series:
    """Taking a pandas data frames row, this function takes the verse id from a given column, checks for its format and converts it to 'standardized' nkv and bkv formats

    :param row: row representing a verse
    :param verse_id_col: column the verse id lives in. The verse_id mentioned here is either in bkv or nkv format – not the later given integer number for quick referencing between tables.
    :return: modified row representing a verse
    """
    verse_id = row[verse_id_col]
    # patterns to check for
    pattern_nkv = r"([1-3A-Za-z]+)\.(\d+)\.(\d+)"
    pattern_nkv_scriptio = r"([1-3A-Za-z]+)\.(inscriptio|subscriptio)"
    pattern_bkv = r"B(\d{2})K(\d+)V(\d+)"
    pattern_bkv_scriptio = (
        r"B(\d{2})K(inscriptio|subscriptio|Inscriptio|Subscriptio)V(\d+)"
    )
    # check data against patterns
    match_nkv = re.match(pattern_nkv, verse_id)
    match_nkv_scriptio = re.match(pattern_nkv_scriptio, verse_id)
    match_bkv = re.match(pattern_bkv, verse_id)
    match_bkv_scriptio = re.match(pattern_bkv_scriptio, verse_id)

    # handle match on nkv schema
    if match_nkv:
        # parts of matched string
        book_name = match_nkv.group(1)
        chapter = match_nkv.group(2)
        verse = match_nkv.group(3)
        # check for book_name in en values of dicts
        for book_num, value in BOOK_INFO.items():
            if value["en"] == book_name:
                row["bkv"] = f"B{book_num}K{chapter}V{verse}"
                row["nkv"] = verse_id
                break
    # handle match on bkv schema
    elif match_bkv:
        book_num = match_bkv.group(1)
        chapter = match_bkv.group(2)
        verse = match_bkv.group(3)
        # check for book_name in en values of dicts
        try:
            book_abb_en = BOOK_INFO[str(book_num)]["en"]
            row["nkv"] = f"{book_abb_en}.{chapter}.{verse}"
            row["bkv"] = verse_id
        except KeyError:
            # If book_num is not in BOOK_INFO, leave nkv and bkv unset
            row["nkv"] = None
            row["bkv"] = None
    # check for sub- or inscriptio
    elif match_nkv_scriptio:
        book_name = match_nkv_scriptio.group(1)
        scriptio = match_nkv_scriptio.group(2)
        # check for book_name in en values of dicts
        for book_num, value in BOOK_INFO.items():
            if value["en"] == book_name:
                row["bkv"] = f"B{book_num}K{scriptio.capitalize()}V0"
                row["nkv"] = f"{book_name}.{scriptio.capitalize()}"
                break
    elif match_bkv_scriptio:
        book_num = match_bkv_scriptio.group(1)
        scriptio = match_bkv_scriptio.group(2)
        # check for book_name in en values of dicts
        book_abb_en = BOOK_INFO[str(book_num)]["en"]
        row["nkv"] = f"{book_abb_en}.{scriptio.capitalize()}"
        row["bkv"] = f"B{book_num}K{scriptio.capitalize()}V0"
    # handle no match
    else:
        row["bkv"] = None
        row["nkv"] = None

    return row


def generate_local_copies(
    verses: pd.DataFrame, gendervoc: pd.DataFrame, bkv: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate local copies of the two given dataframes (verses and gendervoc). The copied verses dataframe only
    contains entries with the given bkv and drops all rows with None in 'text' and 'marks' columns. The copied
    gendervoc dataframe drops rows where variant value is None

    :param verses: dataframe containing the verses
    :param gendervoc: dataframe containing the vocabulary
    :param bkv: bkv to filter for
    :return: tupel of dataframes: one is a copy of verses, the other of names
    """
    # make local copy of verses_df
    local_verses = verses[verses["bkv"] == bkv].copy()
    local_verses.dropna(subset=["text"], inplace=True)

    # make local copy of gendervoc_df
    local_gendervoc = gendervoc.copy()
    local_gendervoc.dropna(subset=["variant"], inplace=True)

    # TODO: DROP UNNECESSARY COLUMNS HERE
    # needed columns of verses: verse_id, text
    # needed columns of words: variant, variantID, wordID

    # return both
    return (local_verses, local_gendervoc)


def search_words(words: pd.DataFrame, verses: pd.DataFrame, blacklist: dict):
    """search verses for given list of words

    :param words: pandas dataframe holding word variants (en_tag,el_tag,variant,gender,type,wordID,variantID)
    :param verses: pandas dataframe holding verses (bkv,text,docID)
    :param blacklist:

    """

    # Add a new column "found" to store lists of variant IDs for each verse
    verses["found_variants"] = None
    verses["missing_names"] = None

    # Set of all variants found in the given verses. Used to check against the variant_id_list to get
    word_id_set_bkv = set()

    # for every verse (row  in verses dataframe)
    for index, verse_row in verses.iterrows():
        verse_text = verse_row["text"]

        # check if current verse_id is blacklisted and set up a set of blacklisted wordIDs
        if verse_row["verse_id"] in blacklist:
            blacklisted_wordIDs = set(blacklist[verse_row["verse_id"]])
        else:
            blacklisted_wordIDs = set()

        # Create an empty set to store matching variants for the current verse.
        variant_id_set_verse = set()

        # Iterate over each row in dataframe_names to search for variants in the current verse
        for _, word_row in words.iterrows():
            # for every row check
            if word_row["wordID"] not in blacklisted_wordIDs:
                # get variant of this word_row
                variant = word_row["variant"]
                # Check if the variant is present in the verse text
                if re.search(rf"\b{re.escape(variant)}\b", verse_text):
                    # write variants wordID to list
                    variant_id = word_row["variantID"]
                    variant_id_set_verse.add(variant_id)
                    word_id_set_bkv.add(word_row["wordID"])

        # add variant_id_list to verse_row column "found"
        verses.at[index, "found_variants"] = variant_id_set_verse

    # for every verse (row  in verses dataframe)
    # for index, verse_row in verses.iterrows():
    #    variant_ids = verse_row["found_variants"]
    #    word_ids = set(words[words["variantID"].isin(variant_ids)]["wordID"])
    #    diff = word_id_set_bkv - word_ids
    #    verses.at[index, "missing_wordIDs"] = diff

    verses["missing_wordIDs"] = verses["found_variants"].apply(
        lambda variant_ids: word_id_set_bkv
        - set(words[words["variantID"].isin(variant_ids)]["wordID"])
    )  # this is the compact form of the 5 lines above


def process_bkv(
    bkv: str,
    out_dir: str,
    verses: pd.DataFrame,
    gendervoc: pd.DataFrame,
    blacklist_dict: dict,
    overwrite: bool = True,
):
    """Search a BKV for names

    :param bkv: verse identifier string like "B01K1V1" to be the search scope
    :param out_dir: directory to write resulting data to
    :param verses: pandas dataframe containing all verses
    :param gendervoc: pandas dataframe containing all gender bound vocabulary
    :param blacklist_dict: TODO: description
    :param overwrite: whether to overwrite existing data
    :return:
    """
    output_file = f"{out_dir}/{bkv}.csv"

    # make out_dir if not already present
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # if file does not yet exist or overwrite is set to True
    if not os.path.exists(output_file) or overwrite:
        # generate local dataframe copies
        (local_verses_df, local_gendervoc_df) = generate_local_copies(
            verses, gendervoc, bkv
        )

        # some dataframes are empty (e.g. "B06K16V24" and "B04K7V53"). On those the search is not to be performed.
        if local_verses_df.empty:
            print(f"Dataframe for {bkv} is empty...")
            return

        # update local_verses_df and get set of found variant ids
        search_words(local_gendervoc_df, local_verses_df, blacklist_dict)

        # Explode the "found" column, drop empty rows, rename columns 'missing' and 'found'
        found = (
            local_verses_df.explode("found_variants")
            .rename(
                columns={"missing_names": "occurrence", "found_variants": "variantID"}
            )
            .dropna(subset=["variantID"])
        )
        # set all entries to True
        found.loc[:, "occurrence"] = True

        def get_word_id(variant_id):
            matches = gendervoc[gendervoc["variantID"] == variant_id]["wordID"]
            return matches.iloc[0] if not matches.empty else None

        found["wordID"] = found["variantID"].apply(get_word_id)

        # Explode the "missing" column, drop empty rows, rename columns 'found' and 'missing'
        missing = (
            local_verses_df.explode("missing_wordIDs")
            .rename(
                columns={"found_variants": "occurrence", "missing_wordIDs": "wordID"}
            )
            .dropna(subset=["wordID"])
        )
        # set all entries to False
        missing.loc[:, "occurrence"] = False

        # merging dataframes of found and missing
        occurrences = pd.concat([found, missing], ignore_index=True)
        # TODO: set occurrences cells with null to -1 for variantID integers, as when occurrence is FALSE,
        #  there will be no variantID given – only the wordID will be present

        # get relevant columns only
        occurrences = occurrences[["verse_id", "variantID", "occurrence", "wordID"]]
        # Writing the DataFrame to a CSV file
        occurrences.to_csv(output_file, index=False)


def get_docID_set(metadata_list_xml: str, all: bool = True) -> set:
    """Retrieve set of docIDs from an XML containing all catalogued manuscripts in the NTVMR.

    :param metadata_list_xml: raw XML string containing all catalogued manuscripts
    :param all: boolean flag indicating if all catalogued manuscripts should be kept
    :return: set of docIDs
    """
    # Read XML data from file
    with open(metadata_list_xml, "r") as file:
        xml_data = file.read()

    # Parse XML
    root = ET.fromstring(xml_data)

    # Initialize set
    doc_ids_set = set()

    # Iterate through Papyri, Majuscules, Minuscules, Lectionaries (docIDs 10000-50000) if all is set t False
    if all:
        # Original loop to add docIDs to the set
        for manuscript in root.findall("manuscript"):
            doc_id = manuscript.get("docID")
            if doc_id is not None:
                doc_ids_set.add(int(doc_id))
    else:
        # Modified loop to add docIDs to the set and remove those above 50000
        for manuscript in root.findall("manuscript"):
            doc_id = manuscript.get("docID")
            if doc_id is not None:
                docID = int(doc_id)
                if docID <= 50000:
                    doc_ids_set.add(docID)

    # Print the set of docIDs smaller than 50000
    return doc_ids_set


def gap_clean(text: str) -> str | None:
    """Removes everything inside brackets except Greek characters, also removes the brackets.

    :param text: Input string containing text with brackets
    :return: Cleaned string with only Greek characters inside the brackets
    """
    try:
        return re.sub(
            r"\[([^\]]*)\]",
            lambda match: "".join(re.findall(r"[Α-Ωα-ω]+", match.group(1))),
            text,
        )
    except TypeError as e:
        print(e, text)
