import json
import os
import random
import re
import time
from datetime import datetime

import constants
import requests
from bs4 import BeautifulSoup


def check_and_create_file(file_path):
    """Create a file after checking its existance

    :param file_path: path to file to be checked
    """
    # Check if the file already exists
    if not os.path.exists(file_path):
        # Get the directory path
        dir_path = os.path.dirname(file_path)

        # Create the directory path if it does not exist
        check_and_create_directory(dir_path)

        # Create the file
        with open(file_path, encoding="utf-8", mode="w") as file:
            file.write("")
            print(f"File created: {file_path}")


def check_and_create_directory(directory):
    """Create a directory after checking its existance

    :param directory: directory to be checked
    """
    # Create the directory path if it does not exist
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Directory created: {directory}")


def url_to_error_log(url: str, reason: str, error_log_file: str):
    """
    Log an error message as JSON to the given log file.
    Each line is a JSON object (JSON Lines format).
    """
    check_and_create_file(error_log_file)

    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",  # ISO 8601
        "reason": reason,
        "url": url,
    }

    with open(error_log_file, encoding="utf-8", mode="a") as error_log:
        error_log.write(json.dumps(log_entry) + "\n")


def download_ntvmr_transcripts(
    docID: int, directory: str, error_log_file: str, overwrite: bool = True
):
    """Download a transcription of a given docID from NTVMR

    :param docID: documentID of the manuscript to download transcription of
    :param directory: directory where to save transcription
    :param error_log_file: Path to the log file
    :param overwrite: boolean to select if file should be overwritten if it already exists
    :return:
    """
    url = f"http://ntvmr.uni-muenster.de/community/vmr/api/transcript/get/?docID={docID}&pageID=ALL&format=teiraw"  # &filterNoise=true
    output_file = f"{directory}/{docID}.xml"
    check_and_create_directory(directory)

    if not os.path.exists(output_file) or overwrite:
        # if file does not already do exist or overwrite is true
        fetch_xml(url, output_file, error_log_file)
    # else:
    #    print(f"File already exists: {output_file}")


def download_igntp_transcripts(ga: str, error_log_file: str, overwrite: bool = True):
    """Download a transcription of a given GA from IGNTP

    :param ga: Gregory Aland number of the manuscript to download transcriptions of
    :param error_log_file: Path to the log file
    :param overwrite: boolean to select if file should be overwritten if it already exists
    :return:
    """

    for directory in constants.IGNTP_DIRS:
        check_and_create_directory(directory)

    # collection of 'API endpoints' for the transcriptions of john and epistulae (as of 05/2025)
    api_dict = [
        {
            "url": f"https://itseeweb.cal.bham.ac.uk/iohannes/transcriptions/greek/NT_GRC_{ga}_John.xml",
            "output_file": f"{constants.IGNTP_JOHN}/NT_GRC_{ga}_John.xml",
        },
        {
            "url": f"https://itseeweb.cal.bham.ac.uk/epistulae/transcriptions/greek/Rom/NT_GRC_{ga}_Rom.xml",
            "output_file": f"{constants.IGNTP_ROM}/NT_GRC_{ga}_Rom.xml",
        },
        {
            "url": f"https://itseeweb.cal.bham.ac.uk/epistulae/transcriptions/greek/1Cor/NT_GRC_{ga}_1Cor.xml",
            "output_file": f"{constants.IGNTP_1COR}/NT_GRC_{ga}_1Cor.xml",
        },
        {
            "url": f"https://itseeweb.cal.bham.ac.uk/epistulae/transcriptions/greek/Gal/NT_GRC_{ga}_Gal.xml",
            "output_file": f"{constants.IGNTP_GAL}/NT_GRC_{ga}_Gal.xml",
        },
        {
            "url": f"https://itseeweb.cal.bham.ac.uk/epistulae/transcriptions/greek/Eph/NT_GRC_{ga}_Eph.xml",
            "output_file": f"{constants.IGNTP_EPH}/NT_GRC_{ga}_Eph.xml",
        },
        {
            "url": f"https://itseeweb.cal.bham.ac.uk/epistulae/transcriptions/greek/Phil/NT_GRC_{ga}_Phil.xml",
            "output_file": f"{constants.IGNTP_PHIL}/NT_GRC_{ga}_Phil.xml",
        },
        {
            "url": f"https://itseeweb.cal.bham.ac.uk/epistulae/transcriptions/greek/Col/NT_GRC_{ga}_Col.xml",
            "output_file": f"{constants.IGNTP_COL}/NT_GRC_{ga}_Col.xml",
        },
    ]

    for api_entry in api_dict:
        if not os.path.exists(api_entry["output_file"]) or overwrite:
            # if file does not already do exist or overwrite is true
            fetch_xml(api_entry["url"], api_entry["output_file"], error_log_file)
        # else:
        #    print(f"File already exists: {api_entry["output_file"]}")


def fetch_xml(
    url: str,
    output_file: str,
    error_log_file: str,
    retries: int = 5,
    delay: float = 2.0,
):
    """
    Fetches an XML file from the given URL, formats it to be human-readable, and writes it to an output file.

    :param url: URL to the XML
    :param output_file: Path to the output file
    :param error_log_file: Path to the log file
    :param retries: Number of retry attempts
    :param delay: Initial delay between retries (in seconds)
    """
    check_and_create_file(error_log_file)

    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=60)

            # Log non-200 responses explicitly
            if response.status_code != 200:
                msg = f"HTTP {response.status_code}: {response.reason}"
                url_to_error_log(url, msg, error_log_file)
                return

            # Check content-type
            content_type = response.headers.get("content-type", "")
            if "text/xml" not in content_type and "application/xml" not in content_type:
                url_to_error_log(
                    url, f"Unexpected content-type: {content_type}", error_log_file
                )
                return

            decoded_text = response.content.decode("utf-8")
            soup = BeautifulSoup(decoded_text, "xml")

            # Check for <error> tag
            if soup.tag == "error":
                url_to_error_log(
                    url, str(soup.get("message", "Unknown XML error")), error_log_file
                )
                return

            # Minify and write XML
            minified_xml = minify_xml(soup)
            with open(output_file, encoding="utf-8", mode="w") as f:
                f.write(minified_xml)
            return  # success

        except Exception as e:
            if attempt < retries - 1:
                sleep_time = delay * (2**attempt) + random.uniform(0, 0.5)
                time.sleep(sleep_time)
            else:
                url_to_error_log(
                    url,
                    f"Failed after {retries} attempts: {type(e).__name__}: {str(e)}",
                    error_log_file,
                )


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


def get_docID_set(metadata_list_xml: str, all: bool = True) -> set:
    """Retrieve set of docIDs from an XML containing all catalogued manuscripts in the NTVMR.

    :param metadata_list_xml: raw XML string containing all catalogued manuscripts
    :param all: boolean flag indicating if all catalogued manuscripts should be kept
    :return: set of docIDs
    """
    # Read XML data from file
    with open(metadata_list_xml, encoding="utf-8", mode="r") as file:
        xml_data = file.read()

    # Parse XML
    soup = BeautifulSoup(xml_data, "xml")

    # Initialize set
    doc_ids_set = set()

    # Iterate through Papyri, Majuscules, Minuscules, Lectionaries (docIDs 10000-50000) if all is set t False
    if all:
        # Original loop to add docIDs to the set
        for manuscript in soup.find_all("manuscript"):
            doc_ids_set.add(int(manuscript.get("docID")))
    else:
        # Modified loop to add docIDs to the set and remove those above 50000
        for manuscript in soup.find_all("manuscript"):
            docID = int(manuscript.get("docID"))
            if docID <= 50000:
                doc_ids_set.add(docID)

    # Print the set of docIDs smaller than 50000
    return doc_ids_set


def filter_set_by_regex(strings: set[str], pattern: str) -> set[str]:
    """TODO: _summary_

    :param strings: _description_
    :param pattern: _description_
    :return: _description_
    """
    regex = re.compile(pattern)
    ga_set = set()

    for string in strings:
        if regex.match(string):
            ga_set.add(string)

    return ga_set


def get_ga_set(metadata_list_xml: str, all: bool = False) -> set:
    """Retrieve set of GAs from an XML containing all catalogued manuscripts in the NTVMR.

    :param metadata_list_xml: raw XML string containing all catalogued manuscripts
    :param all: boolean flag indicating if all catalogued manuscripts should be kept
    :return: set of GAs
    """
    # Read XML data from file
    with open(metadata_list_xml, encoding="utf-8", mode="r") as file:
        xml_data = file.read()

    # Parse XML
    soup = BeautifulSoup(xml_data, "xml")

    # Initialize set
    ga_set = set()

    # Loop to add GAs to the set
    for manuscript in soup.find_all("manuscript"):
        ga_set.add(str(manuscript.get("gaNum")))
    # Remove GAs which are not in Papyri, Majuscules, Minuscules or Lectionaries
    if not all:
        ga_set = filter_set_by_regex(ga_set, r"^[PL]?\d{1,5}(S\d{1,})?$")

    # Print the set of docIDs smaller than 50000
    return ga_set


def minify_xml(xml_content) -> str:
    """Minify XML structure

    :param xml_content: XML to be minified
    :return: minified XML string
    """
    # Convert the parsed XML back to a string, removing unnecessary whitespace
    minified_xml = str(xml_content)
    minified_xml = minified_xml.replace("\n", "").replace("> <", "><")
    return minified_xml
