import io
import json
import os
import random
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup


def check_and_create_file(file_path: str):
    """TODO: _summary_

    :param file_path: _description_
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


def check_and_create_directory(directory: str):
    """TODO: _summary_

    :param directory: _description_
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


def fetch_xml(url: str, output_file: str, error_log_file: str):
    """Fetches an XML file from the given URL, formats it to be human readable and writes it to an output file

    :param url: URL to the XML
    :param output_file: Path to the output file
    :param error_log_file: Path to the log file
    :return:
    """
    check_and_create_file(error_log_file)

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and "text/xml" in response.headers.get(
            "content-type"
        ):
            soup = BeautifulSoup(response.text, "xml")
            # Check for <error> tag with code attribute equal to 1
            if soup.tag == "error":
                url_to_error_log(url, soup.get("message"), error_log_file)
                return
            # Write the string to the output file without any formatting
            minified_xml = str(soup)
            xml_string = minified_xml.replace("\n", "").replace("> <", "><")
            with open(output_file, encoding="utf-8", mode="w") as f:
                f.write(xml_string)
        else:
            url_to_error_log(url, "no xml found", error_log_file)

    except Exception as e:
        url_to_error_log(url, str(e), error_log_file)


def get_docID_set(metadata_list_xml: str, everything: bool = True) -> set:
    """Retrieve set of docIDs from an XML containing all catalogued manuscripts in the NTVMR.

    :param metadata_list_xml: raw XML string containing all catalogued manuscripts
    :param everything: boolean flag indicating if all catalogued manuscripts should be kept
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
    if everything:
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


def fetch_and_format_json(
    url: str,
    output_file: str,
    error_log_file: str,
    retries: int = 5,
    delay: float = 2.0,
):
    """
    Fetches a JSON file from the given URL, formats it to be human-readable, and writes it to an output file.

    :param url: URL to the JSON
    :param output_file: Path to the output file
    :param error_log_file: Path to the log file
    :param retries: Number of retry attempts
    :param delay: Initial delay between retries (in seconds)
    """
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            if (
                response.status_code == 200
                and "application/json" in response.headers.get("content-type", "")
            ):
                data = response.json()
                formatted_json = json.dumps(data, indent=4)

                with open(output_file, "w", encoding="utf-8") as file:
                    file.write(formatted_json)
                return  # success

            else:
                url_to_error_log(url, "no json found", error_log_file)
                return

        except requests.RequestException as e:
            if attempt < retries - 1:
                sleep_time = delay * (2**attempt) + random.uniform(0, 0.5)
                time.sleep(sleep_time)
            else:
                url_to_error_log(
                    url, f"Failed after {retries} attempts: {str(e)}", error_log_file
                )


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
    output_file = path + f"{docID}.json"

    if not os.path.exists(output_file) or overwrite:
        # if file does not already do exist or overwrite is true
        fetch_and_format_json(url, output_file, error_log_file)
    # else:
    #    print(f"File already exists: {output_file}")
