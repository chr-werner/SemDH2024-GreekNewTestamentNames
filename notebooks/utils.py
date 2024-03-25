import io
import json
import os
import pandas as pd
import re
import requests
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

from bs4 import BeautifulSoup
from constants import BOOK_INFO
from dataclasses import dataclass


@dataclass
class Source:
    country: str
    settlement: str
    repository: str
    idno: str


@dataclass
class Verse:
    bkv: str
    text: str  # lorem ipsum text
    marks: str  # ccccu sssss uccc -> unclear: u, clear: c, supplied: s
    # raw: str
    publisher: str


@dataclass
class Manuscript:
    sources: list[Source]
    ga: str
    docID: int
    label: str
    # originYear: {late: int, early: int, content: str}


class TEIFile(object):
    def __init__(self, filepath):
        self.filepath = filepath
        self.soup = read_tei(filepath)

    @property
    def ga(self) -> str:
        try:
            return self.soup.find("title", type="document").get("n")
        except Exception as e:
            print(f"{e} for file {self.filepath}")

    @property
    def publisher(self) -> str:
        content = self.soup.find("name", type="org")
        return get_elem_text(content)

    @property
    def docID(self) -> int | None:
        # TODO BUG: if content is not digits only, a conversion of the ga should be done: as NT_GRC_2816S_Rom.xml
        #  gives key="2816S" but also gives a correct msDesc/msIdentifier type="Liste"
        #  (but this description is not always given)
        try:
            # Try getting "key" attribute from "title" tag with type="document"
            value = self.soup.find("title", type="document").get("key")
        except Exception as e:
            value = None
        if value is None:
            try:
                # If the above fails, try getting text from "msidentifier" tag with type="Liste"
                value = self.soup.find("msidentifier", type="Liste").text
            except Exception as e:
                value = None
        if value is None:
            try:
                # If the above fails, try getting an integer from the filename without extension
                value = int(os.path.splitext(os.path.basename(self.filepath))[0])
            except Exception as e:
                value = None
        return value

    @property
    def label(self) -> str:
        content = self.soup.find("msName")
        return get_elem_text(content)

    @property
    def sources(self) -> list[Source]:
        sources_in_header = self.soup.find_all("msIdentifier")

        sources = []
        for source in sources_in_header:
            country = get_elem_text(source.country)
            settlement = get_elem_text(source.settlement)
            repository = get_elem_text(source.repository)
            idno = get_elem_text(source.idno)

            sources.append(Source(country, settlement, repository, idno))

        return sources

    @property
    def verses(self) -> list[Verse]:
        verses = []

        # get all blocks with verses
        blocks = self.soup.find_all("ab", attrs={"n": True})

        # Iterate through blocks
        for i in range(len(blocks)):
            # list to store w tags
            all_words = []
            # get current block data
            current_soup = blocks[i]
            # get current blocks bkv
            bkv = current_soup.get("n")

            # Check if it's not the last block
            if i < len(blocks) - 1:
                next_soup = blocks[i + 1]
                # Check if both current and next soup objects have 'part' attribute AND are of same bkv
                if (
                    current_soup.get("part") == "I"
                    and next_soup.get("part") == "F"
                    and current_soup.get("n") == next_soup.get("n")
                ):
                    all_words.extend(current_soup.find_all("w"))
                    all_words.extend(next_soup.find_all("w"))
                else:
                    all_words.extend(current_soup.find_all("w"))
            # Handling the last block
            else:
                prev_soup = blocks[i - 1]
                if prev_soup.get("part") == "I" and current_soup.get("part") == "F":
                    break
                else:
                    all_words = current_soup.find_all("w")

            text_reconstructed = concat_text_from_tags_2(all_words)
            # remove diacritics from text
            text_reconstructed = str_remove_diacritics(text_reconstructed)
            marks = get_marks_2(all_words)
            publisher = self.publisher
            # write to object
            verse_description = Verse(bkv, text_reconstructed, marks, publisher)
            # append object to list
            verses.append(verse_description)

        return verses

    @property
    def manuscript(self) -> Manuscript:
        sources = self.sources
        ga = self.ga
        label = self.label
        docID = self.docID

        return Manuscript(sources, ga, docID, label)


def fetch_xml(url: str, output_file: str):
    """Fetches an XML file from the given URL to an output file

    :param url: URL to the XML
    :param output_file: Path to the output file
    :return:
    """
    try:
        response = requests.get(url)
        if response.status_code == 200 and "<?xml" in response.text:
            with open(output_file, "wb") as file:
                file.write(response.content)
            # print(f"Downloaded and saved: {url}")
    except requests.RequestException as e:
        print(f"Error downloading {url}: {e}")


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
    """Fetches an XML file from the given URL, formats it to be human readable and writes it to an output file

    :param url: URL to the XML
    :param output_file: Path to the output file
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


def format_xml(root: ET.Element, output_file: str):
    """Format given xml data and write formatted xml to given file

    :param root: root element of xml
    :param output_file: path string to write file to
    :return:
    """
    # parse and indent data
    tree = ET.ElementTree(root)
    ET.indent(tree, level=0)
    # Check if the output directory exists, if not, create it
    output_directory = os.path.dirname(output_file)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    # write data to file
    tree.write(output_file, encoding="utf-8")


def fetch_json(url: str, output_file: str):
    """Fetches an JSON file from the given URL to an output file

    :param url: URL to the JSON data
    :param output_file: Path to the output file
    :return:
    """
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(output_file, "wb") as file:
                file.write(response.content)
            # print(f"Downloaded and saved: {url}")
    except requests.RequestException as e:
        print(f"Error downloading {url}: {e}")


def fetch_and_format_json(url: str, output_file: str, error_log_file: str):
    """Fetches an JSON file from the given URL, formats it to be human readable and writes it to an output file

    :param url: URL to the JSON
    :param output_file: Path to the output file
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


def str_remove_diacritics(s: str) -> str:
    """Normalize string by removing accents and converting to lower case.

    - unicodedata.normalize('NFKD', s): normalizes the input Unicode string s using NFKD normalization. Valid normalization forms are ‘NFC’, ‘NFKC’, ‘NFD’, and ‘NFKD’.
    - (c for c in ...): This is a generator expression that iterates over each character c in the normalized string obtained in the previous step.
    - if unicodedata.category(c) != 'Mn': This condition checks whether the Unicode character c belongs to the category 'Mn' (Mark, Non-Spacing). Characters in this category are combining characters that modify the meaning of the preceding base character. The condition filters out all combining characters from the normalized string.

    :param s: String to be normalized.
    :return:  normalized string
    """
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if unicodedata.category(c) != "Mn"
    ).lower()


def df_remove_diacritics(df: pd.DataFrame, columns_to_process: list[str]):
    """Cleanup a data frame (inplace) by removing diacritics from given columns

    :param df: pandas data frame to be cleaned
    :param columns_to_process: list of strings of columns names to be processed
    :return:
    """
    # remove diacritics from all columns named in columns_to_process
    for col in columns_to_process:
        df[col] = df[col].apply(
            lambda x: str_remove_diacritics(x) if pd.notnull(x) else x
        )


def string_to_list(value):
    """Splits an input into a list if input is a comma separated string

    :param value:
    :return:
    """
    if isinstance(value, str):
        alt_set = set(value.split(","))
        return list(alt_set)
    else:
        return value  # If not a string, return the original value


def read_tei(tei_file_path: str) -> BeautifulSoup:
    """Read a TEI file with beautiful soup

    :param tei_file_path: file path to TEI file
    :return: BeautifulSoup object of TEI file
    """
    try:
        with open(tei_file_path, "r") as tei:
            soup = BeautifulSoup(tei, "xml")
            return soup
    except Exception as exception:
        print("An error occurred:", exception)


def get_elem_text(elem, default="") -> str:
    """Get text of soup element

    :param elem: soup object element
    :param default: fallback to be returned if no text was found in element
    :return: text of element or default value
    """
    try:
        if elem:
            return elem.getText()
        else:
            return default
    except Exception as exception:
        print("An error occurred:", exception)


def concat_text_from_tags_2(tags: list) -> str:
    """concatenate texts of multiple tags to space separated string

    :param tags: list of tags to concatenate text from
    :return: string of tag texts
    """
    words = []
    prev_index = None  # Initialize previous index

    # Extract text from each 'w' tag and its child elements
    for i, tag in enumerate(tags):
        # Check if the tag has an attribute called part="F"
        if tag.get("part") == "F":
            # Save the index of the tag with part="F"
            prev_index = i

        # Filter out text from "note", "lb", "cb" sub tags
        text_parts = [
            part.get_text(separator="", strip=True)
            for part in tag.contents
            if part.name not in ["note", "lb", "cb"]
        ]

        word = "".join([item for item in text_parts if item != ""])

        # If previous index exists, merge it with the previous word
        if prev_index is not None and i != 0:
            words[-1] += text_parts[0]  # Merge previous index with previous word
            prev_index = None
        else:
            words.append(word)

    return " ".join(words)


def concat_text_from_tags(tags: list) -> str:
    """concatenate texts of multiple tags to space separated string

    :param tags: list of tags to concatenate text from
    :return: string of tag texts
    """
    words = []

    # Extract text from each 'w' tag and its child elements
    for tag in tags:
        # Filter out text from "note", "lb", "cb" sub tags
        text_parts = [
            part.get_text(separator="", strip=True)
            for part in tag.contents
            if part.name not in ["note", "lb", "cb"]
        ]
        words.append("".join([item for item in text_parts if item != ""]))

    return " ".join(words)


def concat_raw_text_from_tags(tags: list, exception_list: list) -> str:
    """Concatenate texts of multiple tags to space separated string

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


def replace_characters(tag, mark: str, replacement: str):
    """Helper function to replace characters

    :param tag:
    :param mark:
    :param replacement:
    :return:
    """
    for child in tag.children:
        if child.name == mark:
            child.string = replacement * len(child.text)


def get_marks(tags: list) -> str:
    """Function to extract weather a tag is supplied or unclear

    :param tags: list of xml tags
    :return: string of characters in range(c,s,u)
    """
    word_marks = []
    # Replace characters based on conditions
    for tag in tags:
        replace_characters(tag, "supplied", "s")
        replace_characters(tag, "unclear", "u")
        text = tag.get_text(separator="", strip=True)
        # replace every char that is not a 'u' or 's' with a 'c'
        text = "".join(["c" if char not in ["s", "u"] else char for char in text])

        word_marks.append(text)

    return " ".join(word_marks)


def get_marks_2(tags: list) -> str:
    """Second iteration of get_marks()

    :param tags:
    :return:
    """
    marks = []
    prev_index = None  # Initialize previous index

    # Replace characters based on conditions
    # Extract text from each 'w' tag and its child elements
    for i, tag in enumerate(tags):
        # Check if the tag has an attribute called part="F"
        if tag.get("part") == "F":
            # Save the index of the tag with part="F"
            prev_index = i

        replace_characters(tag, "supplied", "s")
        replace_characters(tag, "unclear", "u")
        text = tag.get_text(separator="", strip=True)

        # replace every char that is not a 'u' or 's' with a 'c'
        text = "".join(["c" if char not in ["s", "u"] else char for char in text])

        # If previous index exists, merge it with the previous word
        if prev_index is not None and i != 0:
            marks[-1] += text  # Merge previous index with previous word
            prev_index = None
        else:
            marks.append(text)

    return " ".join(marks)


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


def ga_to_docID(row: pd.Series) -> int:
    """Convert the GA string corresponding docID for a given row of a pandas data frame

    :param row: pandas data frame row
    :return: docID integer
    """
    # Get ga from row data
    ga = row["ga"]

    # Compile the regular expression pattern
    pattern = re.compile(r"([0-9]\d*)")

    # Remove non-digits from ga
    ga_digits = re.search(pattern, ga).group()

    if ga[0] == "P":
        return 10000 + int(ga_digits)
    elif ga[0] == "0":
        return 20000 + int(ga_digits)
    elif ga[0].isdigit():
        return 30000 + int(ga_digits)
    elif ga[0] == "L":
        return 40000 + int(ga_digits)
    else:
        raise ValueError(
            f"Invalid input: cannot determine document ID for the given input. {ga},{ga_digits}"
        )


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

    :param row: pandas data frame row
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
        else:
            return None

        return f"B{book_num}K{chapter}V{verse}"
    # handle match on bkv schema
    elif match_bkv:
        return bkv
    # handle no match (Rom.Inscriptio etc.)
    else:
        return None


def convert_bkv2nkv(row: pd.Series) -> str | None:
    """Convert bkv values to nkv in a pandas data frame row

    :param row: pandas data frame row
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


def generate_transcription_url(row: pd.Series) -> str | None:
    """Generate a transcription URL for a pandas data frame row which has a nkv and docID assigned, as well as is sourced from the ntvmr

    :param row: pandas data frame row to generate transcription URL for
    :return: link string or NONE
    """
    try:
        nkv = row["nkv"]
        docID = int(row["docID"])
        source = row["source"]

        if (nkv != None) and (docID != None) and (source == "ntvmr"):
            return f"https://ntvmr.uni-muenster.de/community/vmr/api/transcript/get/?docid={docID}&indexContent={nkv}&format=xhtml"
        else:
            return None
    except:
        return None


def generate_local_copies(
    verses: pd.DataFrame, gendervoc: pd.DataFrame, bkv: str
) -> (pd.DataFrame, pd.DataFrame):
    """Generate local copies of the two given data frames (verses and gendervoc).
    The copied verses data frame only contains entries with the given bkv and drops all rows with None in 'text' and 'marks' columns.
    The copied gendervoc data frame drops rows where variant value is None

    :param verses: data frame containing the verses
    :param gendervoc: data frame containing the vocabulary
    :param bkv: bkv to filter for
    :return: tuple of data frames: one is a copy of verses, the other of names
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

    :param words: pandas dataframe holding word variants (en_tag,el_tag,variant,gender,type,wordID,variantID)
    :param verses: pandas dataframe holding verses (bkv,text,docID)

    """

    # Add a new column "found" to store lists of variant IDs for each verse
    verses["found"] = None
    verses["missing"] = None

    # Set of all word ids (indirectly also their variants) found in the given verses. Used to check against the variant_id_list to get
    word_id_set_bkv = set()

    # for every verse (row  in verses dataframe)
    for index, verse_row in verses.iterrows():
        verse_text = verse_row["text"]

        # Create an empty set to store matching variants for the current verse. A list of variantIDs is used
        # instead of a set, as there is the possibility that a variant is occurring multiple times in a verse
        # word_id_list = []
        word_id_set_verse = set()

        # Iterate over each row in dataframe_names to search for variants in the current verse
        for _, word_row in words.iterrows():
            # get variant of this word_row
            variant = word_row["variant"]
            # Check if the variant is present in the verse text
            # TODO BUG: returns variant one time, although it is present several times
            # Temporary fix: using the wordID only
            if re.search(rf"\b{re.escape(variant)}\b", verse_text):
                # write variants wordID to list
                word_id = word_row["wordID"]
                word_id_set_verse.add(word_id)
                word_id_set_bkv.add(word_id)

        # add variant_id_list to verse_row column "found"
        verses.at[index, "found"] = word_id_set_verse

    # for every verse (row  in verses dataframe)
    verses["missing"] = verses.apply(
        lambda row: word_id_set_bkv - set(row["found"]), axis=1
    )


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

        # some data frames are empty (e.g. "B06K16V24" and "B04K7V53"). On those the search is not to be performed.
        if local_verses_df.empty:
            print(f"Dataframe for {bkv} is empty...")
            return

        # update local_verses_df and get set of found variant ids
        search_words(local_gendervoc_df, local_verses_df)

        # Explode the "found" column, drop empty rows, rename columns 'missing' and 'found'
        found = (
            local_verses_df.explode("found")
            .rename(columns={"missing": "occurrence", "found": "wordID"})
            .dropna(subset=["wordID"])
        )
        # set all entries to True
        found.loc[:, "occurrence"] = True

        # Explode the "missing" column, drop empty rows, rename columns 'found' and 'missing'
        missing = (
            local_verses_df.explode("missing")
            .rename(columns={"found": "occurrence", "missing": "wordID"})
            .dropna(subset=["wordID"])
        )
        # set all entries to False
        missing.loc[:, "occurrence"] = False

        # merging dataframes of found and missing
        occurrences = pd.concat([found, missing], ignore_index=True)

        # Writing the DataFrame to a CSV file
        occurrences.to_csv(output_file, index=False)


def get_docID_set(metadata_list_xml: str) -> set:
    # Read XML data from file
    with open(metadata_list_xml, "r") as file:
        xml_data = file.read()

    # Parse XML
    root = ET.fromstring(xml_data)

    # Initialize set
    doc_ids_set = set()

    # Iterate through manuscripts
    for manuscript in root.findall("manuscript"):
        docID = int(manuscript.get("docID"))
        if docID < 50000:
            doc_ids_set.add(docID)

    # Print the set of docIDs smaller than 50000
    return doc_ids_set
