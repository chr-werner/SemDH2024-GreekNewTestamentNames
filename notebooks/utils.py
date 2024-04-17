import io
import json
import os
import pandas as pd
import re
import requests
import xml.etree.ElementTree as ET
import zipfile

from constants import BOOK_INFO
from TEIFile import TEIFile
from converters import tei_to_verses_dict, tei_to_manuscript_dict


def url_to_error_log(url: str, reason: str, error_log_file: str):
    """Print an error message to given log file

    :param url: Url string which produced an error
    :param reason: the error text
    :param error_log_file: path to log file
    :return:
    """
    with open(error_log_file, "a") as error_log:
        error_log.write(f"{url}; {reason}\n")


def fetch_and_format_xml(url: str, output_file: str, error_log_file: str):
    """Fetches an XML file from the given URL, formats it to be humanreadable and writes it to an output file

    :param url: URL to the XML
    :param output_file: Path to the output file
    :param error_log_file: Path to the log file
    :return:
    """
    try:
        response = requests.get(url)
        if response.status_code == 200 and "text/xml" in response.headers.get(
            "content-type"
        ):
            root = ET.fromstring(response.text)

            # Check for <error> tag with code attribute equal to 1
            if root.tag == "error":
                url_to_error_log(url, root.get("message"), error_log_file)
                return

            tree = ET.ElementTree(root)
            ET.indent(tree, level=0)
            tree.write(output_file, encoding="utf-8")
        else:
            url_to_error_log(url, "no xml found", error_log_file)

    except Exception as e:
        url_to_error_log(url, str(e), error_log_file)


def check_xml(file_path: str, parser) -> str | None:
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


def fetch_and_format_json(url: str, output_file: str, error_log_file: str):
    """Fetches an JSON file from the given URL, formats it to be humanreadable and writes it to an output file

    :param url: URL to the JSON
    :param output_file: Path to the output file
    :param error_log_file: Path to the log file
    :return:
    """
    try:
        response = requests.get(url)
        if response.status_code == 200 and "application/json" in response.headers.get(
            "content-type"
        ):
            data = response.json()
            formatted_json = json.dumps(data, indent=4)

            with open(output_file, "w", encoding="utf-8") as file:
                file.write(formatted_json)
        else:
            url_to_error_log(url, "no json found", error_log_file)

    except requests.RequestException as e:
        url_to_error_log(url, str(e), error_log_file)


def fetch_and_extract_zip(url: str, extract_dir: str):
    """Fetches and extracts a zip file from the given URL to given directory

    :param url: URL to the ZIP
    :param extract_dir: Output directory where ZIP should be extracted to
    :return:
    """
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                os.makedirs(extract_dir, exist_ok=True)
                # Extract only XML files from the ZIP file
                # Filter XML files and extract only those not containing "*MAC*"
                xml_files = [
                    f
                    for f in zip_ref.namelist()
                    if f.lower().endswith(".xml") and "__MAC" not in f
                ]
                for xml_file in xml_files:
                    zip_ref.extract(xml_file, extract_dir)
        else:
            print("Failed to download the file")
    except requests.RequestException as e:
        print(f"Error downloading {url}: {e}")


def download_ntvmr_transcripts(
    docID: int, path: str, error_log_file: str, overwrite: bool = True
):
    """Download a transcription of a given docID from NTVMR

    :param docID: documentID of the manuscript to download transcription of
    :param path: directory where to save transcription
    :param error_log_file: Path to the log file
    :param overwrite: boolean to select if file should be overwritten if it already exists
    :return:
    """
    url = f"http://ntvmr.uni-muenster.de/community/vmr/api/transcript/get/?docID={docID}&pageID=ALL&format=teiraw"  # &filterNoise=true
    output_file = f"{path}/{docID}.xml"

    if not os.path.exists(output_file) or overwrite:
        # if file does not already do exist or overwrite is true
        fetch_and_format_xml(url, output_file, error_log_file)
    # else:
    #    print(f"File already exists: {output_file}")


def download_ntvmr_manuscripts(
    docID: int, path: str, error_log_file: str, overwrite: bool = True
):
    """Download metadata of a given docID from NTVMR

    :param docID: documentID of the manuscript to download metadata of
    :param path: directory where to save metadata file
    :param error_log_file: Path to the log file
    :param overwrite: boolean to select if file should be overwritten if it already exists
    :return:
    """
    url = f"https://ntvmr.uni-muenster.de/community/vmr/api/metadata/manuscript/get/?docID={docID}&detail=10&format=json"
    output_file = f"{path}/{docID}.json"

    if not os.path.exists(output_file) or overwrite:
        # if file does not already do exist or overwrite is true
        fetch_and_format_json(url, output_file, error_log_file)
    # else:
    #    print(f"File already exists: {output_file}")


def concat_raw_text_from_tags(tags: list, exception_list: list) -> str:
    """Concatenate texts of multiple tags to space seperated string

    :param tags: list of tags to concatenate text from
    :param exception_list: child tags to ignore in concatenation process
    :return: string of tag texts
    """
    words = []

    for tag in tags:
        for child in tag.children:
            if child.name not in exception_list:
                if child.string:
                    words.append(child.string.strip())

    return " ".join(words)


def get_data_from_tei(tei_file_path: str) -> tuple:
    """Wrapper function to extract manuscript and verse data from TEI file

    :param tei_file_path: TEI file path
    :return: tupel with manuscript and verses data
    """
    tei = TEIFile(tei_file_path)
    # check for source from filepath # TODO: better use the tei file if possible
    if "ntvmr" in str(tei_file_path):
        source = "ntvmr"
    elif "igntp" in str(tei_file_path):
        source = "igntp"
    else:
        source = None

    verses = tei_to_verses_dict(tei, source)
    manuscript = tei_to_manuscript_dict(tei, source)

    return manuscript, verses


def fix_bkv(row: pd.Series) -> str | None:
    """Fix the bkv column, by checking and converting nkv entries

    :param row: pandas dataframe row
    :return: bkv string or NONE
    """
    bkv = row["bkv"]
    # patterns to check for
    pattern_nkv = r"([1-3A-Za-z]+)\.(\d+)\.(\d+)"
    pattern_bkv = r"B(\d{2})K(\d+)V(\d+)"
    # check data against patterns
    match_nkv = re.match(pattern_nkv, bkv)
    match_bkv = re.match(pattern_bkv, bkv)

    # handle match on nkv schema
    if match_nkv:
        # parts of matched string
        book_name = match_nkv.group(1)
        chapter = match_nkv.group(2)
        verse = match_nkv.group(3)
        # check for boo_name in en values of dicts
        for key, value in BOOK_INFO.items():
            if value["en"] == book_name:
                book_num = key
                break

        return f"B{book_num}K{chapter}V{verse}"
    # handle match on bkv schema
    elif match_bkv:
        return bkv
    # handle no match (Rom.Inscriptio etc.)
    else:
        return None


def generate_transcription_url(row: pd.Series) -> str | None:
    """Generate a transcription URL for a pandas dataframe row which has a nkv and docID assigned, as well as is
    sourced from the NTVMR.

    :param row: pandas dataframe row to generate transcription URL for
    :return: link string or NONE
    """
    try:
        nkv = row["nkv"]
        docID = int(row["docID"])
        source = row["source"]

        if (nkv is not None) and (docID is not None) and (source == "ntvmr"):
            return f"https://ntvmr.uni-muenster.de/community/vmr/api/transcript/get/?docid={docID}&indexContent={nkv}&format=xhtml"
        else:
            return None
    except:
        return None


def generate_local_copies(
    verses: pd.DataFrame, gendervoc: pd.DataFrame, bkv: str
) -> (pd.DataFrame, pd.DataFrame):
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
    local_verses.dropna(subset=["text", "marks"], inplace=True)

    # make local copy of gendervoc_df
    local_gendervoc = gendervoc.copy()
    local_gendervoc.dropna(subset=["variant"], inplace=True)

    # return both
    return (local_verses, local_gendervoc)


def search_words(words: pd.DataFrame, verses: pd.DataFrame):
    """search verses for given list of words

    TODO: search should be done on unique variantID

    :param words: pandas dataframe holding word variants (en_tag,el_tag,variant,gender,type,wordID,variantID)
    :param verses: pandas dataframe holding verses (bkv,text,docID)

    """

    # Add a new column "found" to store lists of variant IDs for each verse
    verses["found_variants"] = None
    verses["missing_names"] = None

    # Set of all variants found in the given verses. Used to check against the variant_id_list to get
    word_id_set_bkv = set()

    # for every verse (row  in verses dataframe)
    for index, verse_row in verses.iterrows():
        verse_text = verse_row["text"]

        # Create an empty set to store matching variants for the current verse.
        variant_id_set_verse = set()

        # Iterate over each row in dataframe_names to search for variants in the current verse
        for _, word_row in words.iterrows():
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
    overwrite: bool = True,
):
    """Search a BKV for names

    :param bkv: verse identifier string like "B01K1V1" to be the search scope
    :param out_dir: directory to write resulting data to
    :param verses: pandas dataframe containing all verses
    :param gendervoc: pandas dataframe containing all gender bound vocabulary
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
        search_words(local_gendervoc_df, local_verses_df)

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
        found["wordID"] = found["variantID"].apply(
            lambda variant_id: gendervoc.loc[
                gendervoc["variantID"] == variant_id, "wordID"
            ].values[0]
        )

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

        occurrences.drop(columns=["missing_wordIDs", "missing_names"], inplace=True)
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
            doc_ids_set.add(int(manuscript.get("docID")))
    else:
        # Modified loop to add docIDs to the set and remove those above 50000
        for manuscript in root.findall("manuscript"):
            docID = int(manuscript.get("docID"))
            if docID <= 50000:
                doc_ids_set.add(docID)

    # Print the set of docIDs smaller than 50000
    return doc_ids_set
