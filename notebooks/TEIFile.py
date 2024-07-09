from bs4 import BeautifulSoup
from dateutil import parser as dtparser
import unicodedata
import re


class TEIFile(object):
    def __init__(self, filepath, clear_only, verbose):
        self._filepath = filepath
        self._soup = self._read_tei(self._filepath)
        self._clear_only = clear_only
        self.verbose = verbose

    # All properties below are currently read only

    @property
    def ga(self) -> str or None:
        """Property returning the Gregory Aaland (GA) Number

        :return: Gregory Aaland (GA) Number as String
        """
        try:
            return self._soup.find("title", type="document").get("n")
        except Exception as e:
            print(f"No title; {e} for file {self._filepath}") if self.verbose else None
            return None

    @property
    def publisher(self) -> list or None:
        """Property returning the names of publishing institutions/persons

        :return: List of names of publishing institutions/persons
        """
        publisher_names = []
        try:
            for name_tag in self._soup.find("publisher").find_all("name"):
                publisher_names.append(name_tag.text)
            return publisher_names
        except Exception as e:
            (
                print(f"No publisher; {e} for file {self._filepath}")
                if self.verbose
                else None
            )
            return None

    @property
    def founder(self) -> str or None:
        """Property returning the name of founding institution

        :return: name of founding institution
        """
        try:
            return self._soup.find("funder").getText()
        except Exception as e:
            (
                print(f"No founder; {e} for file {self._filepath}")
                if self.verbose
                else None
            )
            return None

    @property
    def label(self) -> str or None:
        """Property returning the name of the document

        :return: name of the document
        """
        try:
            return self._soup.find("msName").getText()
        except Exception as e:
            print(f"No label; {e} for file {self._filepath}") if self.verbose else None
            return None

    @property
    def sponsor(self) -> set or None:
        """Property returning the names of sponsoring institutions/persons

        :return: names of sponsoring institutions/persons
        """
        sponsor_names = set()
        try:
            for name_tag in self._soup.find("publisher").find_all("name"):
                sponsor_names.add(name_tag.text)
            return sponsor_names
        except Exception as e:
            (
                print(f"No sponsor; {e} for file {self._filepath}")
                if self.verbose
                else None
            )
            return None

    @property
    def edition(self) -> ():
        """Property returning the editions version and date (in YYYY-MM-DD format) as tuple

        :return: editions version and date
        """
        try:
            edition = self._soup.find("edition").get("n")
        except Exception as e:
            (
                print(f"No edition; {e} for file {self._filepath}")
                if self.verbose
                else None
            )
            edition = None

        try:
            date_str = self._soup.find("edition").find("date").getText()
            date = dtparser.parse(date_str).strftime("%Y-%m-%d")
        except Exception as e:
            (
                print(f"No edition date; {e} for file {self._filepath}")
                if self.verbose
                else None
            )
            date = None

        return edition, date

    @property
    def publishing_date(self) -> str or None:
        """Property returning the publishing date of the document in YYYY-MM-DD Format

        :return: publishing date of the document
        """
        try:
            date_str = self._soup.find("publicationStmt").find("date").getText()
            return dtparser.parse(date_str).strftime("%Y-%m-%d")
        except Exception as e:
            (
                print(f"No publishing date; {e} for file {self._filepath}")
                if self.verbose
                else None
            )
            return None

    @property
    def alt_identifiers(self) -> dict or None:
        """Property returning alternative identifiers for a documents

        :return: tuples of alternative identifier name and number in this schema
        """
        alt_identifiers = {}
        try:
            for alt_identifier in self._soup.find_all("altIdentifier"):
                type = alt_identifier.get("type")
                value = alt_identifier.find("idno").getText()
                alt_identifiers[type] = value
            return alt_identifiers
        except Exception as e:
            (
                print(f"No alternative identifiers; {e} for file {self._filepath}")
                if self.verbose
                else None
            )
            return alt_identifiers

    # @property
    # def witnesses(self) -> set or None:
    #    """Property returning the list of witnesses in the document
    #       TODO: this should/could be a method
    #    :return: witnesses in the document
    #    """
    #    witnesses = set()
    #    try:
    #        for witness in self._soup.find("listWit").find_all("witness"):
    #            witnesses.add(witness.get("xml:id"))
    #        return witnesses
    #    except Exception as e:
    #        (
    #            print(f"No witnesses; {e} for file {self._filepath}")
    #            if self.verbose
    #            else None
    #        )
    #        return None

    @property
    def encoding_version(self) -> str or None:
        """Property returning the encoding version (by the IGNTP) of the document

        :return: witnesses in the document
        """
        try:
            return self._soup.find("encodingDesc").get("n")
        except Exception as e:
            (
                print(f"No encoding version; {e} for file {self._filepath}")
                if self.verbose
                else None
            )
            return None

    # @property
    # def revisions(self) -> set or None:
    #    """Property returning revision history of the document
    #       TODO: this should/could be a method
    #    :return: list of tuples of revision id, date of the revision and description
    #    """
    #    revisions = set()
    #    try:
    #        for revision in self._soup.find("revisionDesc").find_all("change"):
    #            no = revision.get("n")
    #            date = revision.get("when")
    #            description = revision.getText()
    #            revisions.add((no, date, description))
    #        return revisions
    #    except Exception as e:
    #        (
    #            print(f"No revision; {e} for file {self._filepath}")
    #            if self.verbose
    #            else None
    #        )
    #        return None

    # @property
    # def resp(self) -> ():
    #    """Property returning the response object of the document
    #       TODO: this should/could be a method
    #    :return: triple of lists of creators, transcribers and reconcilers
    #    """
    #    creators = []
    #    transcribers = []
    #    reconcilers = []
    #    try:
    #        for respStmt in self._soup.find_all("respStmt"):
    #            resp = respStmt.find("resp").text
    #            name = respStmt.find("name").text
    #            # Check the type of responsibility and append to the corresponding list
    #            if resp == "Created by":
    #                creators.append(name)
    #            elif resp == "Transcribed by":
    #                transcribers.append(name)
    #            elif resp == "Reconciled by":
    #                reconcilers.append(name)
    #        return creators, transcribers, reconcilers
    #    except Exception as e:
    #        (
    #            print(f"No transcriber data; {e} for file {self._filepath}")
    #            if self.verbose
    #            else None
    #        )
    #        return None

    # @property
    # def lections(self) -> set or None:
    #    """Property returning the set of lections in the document
    #       TODO: this should/could be a method
    #    :return: set of lections in document
    #    """
    #    lections = set()
    #    try:
    #        for lection in self._soup.find_all("div", type="lection"):
    #            # remove all spaces from lection string
    #            lections.add(re.sub(r"\s+", "", lection.get("n")))
    #        return lections
    #    except Exception as e:
    #        (
    #            print(f"No lections; {e} for file {self._filepath}")
    #            if self.verbose
    #            else None
    #        )
    #        return None

    # @property
    # def books(self) -> set or None:
    #    """Property returning the set of books in the document
    #       TODO: this should/could be a method
    #    :return: set of books in the document
    #    """
    #    books = set()
    #    try:
    #        # Find all <div> elements with type="lection"
    #        book_divs = self._soup.find_all("div", type="book")
    #        # Extract the values of the "n" attribute from each <div> element
    #        for book in book_divs:
    #            books.add(book.get("n"))
    #        # Convert the list to a set to remove duplicates
    #        return books
    #    except Exception as e:
    #        print(f"No books; {e} for file {self._filepath}") if self.verbose else None
    #        return None

    @property
    def verses(self) -> set or None:
        """Property returning the set of verses in the document

        :return: set of verses in the document
        """
        verses = []
        try:
            # Find all <div> elements with type="lection"
            verse_divs = self._soup.find_all("ab", attrs={"n": True})
            # Extract the values of the "n" attribute from each <div> element
            for book in verse_divs:
                verses.append(book.get("n"))
            # Convert the list to a set to remove duplicates
            return set(verses)
        except Exception as e:
            print(f"No verses; {e} for file {self._filepath}") if self.verbose else None
            return None

    # @property
    # def nomsac(self) -> set or None:
    #    """Property returning the list of nomina sarca in the document
    #       TODO: this should/could be a method
    #    :return: nomina sacra in the document
    #    """
    #    nomsac = set()
    #    try:
    #        for nom in self._soup.find_all("abbr", type="nomSac"):
    #            # if clear_only is set, we only want to get nomina sacra which are not supplied or unclear
    #            if self._clear_only and (
    #                nom.parent.name in ["supplied", "unclear"]
    #                or nom.find(name=["supplied", "unclear"])
    #            ):
    #                nomsac.add(nom.getText(strip=True))
    #            else:
    #                nomsac.add(nom.getText(strip=True))
    #        # Convert the list to a set to remove duplicates
    #        return nomsac
    #    except Exception as e:
    #        (
    #            print(f"No nomina sacra; {e} for file {self._filepath}")
    #            if self.verbose
    #            else None
    #        )
    #        return None

    # @property
    # def unspecified_supply(self) -> bool:
    #    """Check if an unspecified supplied tag is present in the document, which indicates a faulty transcription
    #       TODO: this should/could be a method
    #    :return: True if unspecified supplied tag is present in the document
    #    """
    #    try:
    #        if self._soup.find("supplied", reason="unspecified"):
    #            return True
    #        else:
    #            return False
    #    except Exception as e:
    #        (
    #            print(f"No unspecified supplied tags; {e} for file {self._filepath}")
    #            if self.verbose
    #            else None
    #        )
    #        return False

    @property
    def transcriptions(self) -> list[dict]:
        # TODO: split into sub functions as currently too much is going on here, also for debugging
        # TODO: test when function is split into sub functions
        """Property returning the transcriptions of verses of the document

        :return: dictionary of the documents structure
        """
        transcriptions_list = []

        # iterate through all known verse_ids in document
        for idx, verse_id in enumerate(self.verses, start=1):
            # verbose output
            if self.verbose:
                print(f"Verse {idx} of {len(self.verses)}")
            # get all ab tags of verse by soup.find_all (generates an ordered list, beginning at the start of the document)
            verse_parts = self._soup.find_all("ab", attrs={"n": verse_id})

            while verse_parts:
                # get first entry
                first_part = verse_parts.pop(0)
                # try to get parent lection
                lection_div = first_part.find_parent("div", {"type": "lection"})

                # if part is a 'I' Part
                if first_part.get("part") == "I" and len(verse_parts) > 0:
                    # also get the followup part ('F')
                    second_part = verse_parts.pop(0)
                    # merge followup into first part
                    first_part.extend(second_part.contents)
                    # merge parted words by finding all <w> tags with attribute part='F'
                    part_f_tag = first_part.find("w", attrs={"part": "F"})
                    # check if one is found
                    if part_f_tag:
                        # merge them with previous sibling
                        preceding_w_tag = part_f_tag.find_previous_sibling("w")
                        if preceding_w_tag:
                            # get text of both word tags
                            combined_text = (
                                preceding_w_tag.get_text() + part_f_tag.get_text()
                            )
                            # create new word tag
                            new_tag = self._soup.new_tag("ns0:w", part="combined")
                            new_tag.string = combined_text
                            # Replace the original tags with the new tag
                            preceding_w_tag.insert_after(new_tag)
                            preceding_w_tag.decompose()
                            part_f_tag.decompose()
                    verse_transcript = self._get_verse_transcription(first_part)

                # else get the transcription of one
                else:
                    verse_transcript = self._get_verse_transcription(first_part)

                transcriptions_list.append(
                    {
                        "lection": lection_div["n"] if lection_div else None,
                        "verse": verse_id,
                        "transcript": self._str_remove_diacritics(
                            verse_transcript
                        ).lower(),
                    }
                )

        return transcriptions_list

    @property
    def source(self) -> str or None:
        """Property returning the source of the document

        :return: download source of the document
        """
        if "ntvmr" in str(self._filepath):
            return "ntvmr"
        elif "igntp" in str(self._filepath):
            return "igntp"
        else:
            return None

    @staticmethod
    def _read_tei(tei_file_path: str) -> BeautifulSoup:
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

    @staticmethod
    def _str_remove_diacritics(s: str) -> str:
        """Normalize string by removing accents and converting to lower case.

        - unicodedata.normalize('NFKD', s): normalizes the input Unicode string s using NFKD normalization. Valid normalization forms are ‘NFC’, ‘NFKC’, ‘NFD’, and ‘NFKD’.
        - (c for c in ...): This is a generator expression that iterates over each character c in the normalized string obtained in the previous step.
        - if unicodedata.category(c) != 'Mn': This condition checks whether the Unicode character c belongs to the category 'Mn' (Mark, Non-Spacing). Characters in this category are combining characters that modify the meaning of the preceding base character. The condition filters out all combining characters from the normalized string.

        :param s: String to be normalized.
        :return:  normalized string
        """
        return "".join(
            c
            for c in unicodedata.normalize("NFKD", s)
            if unicodedata.category(c) != "Mn"
        )

    @staticmethod
    def _str_remove_punctuation(s: str) -> str:
        """Strip punctuation from input string

        :param s: string to strip punctuation from
        :return: string without punctuation
        """
        # remove everything expect characters, spaces, '[' and ']'
        s = re.sub(r"[^\w\s\[\]]", "", s)
        # normalize by removing multiple consecutive whitespaces
        s = re.sub(r"\s+", " ", s)
        # remove leading/trailing whitespaces
        return s.strip()

    @staticmethod
    def _handle_gap(gap_object: BeautifulSoup) -> str:
        """Function to get information from gap tag

        :param gap_object: bs4 object containing the gap tag
        :return: string of the gap reason and description
        """
        # this oneliner is iterating over the attributes given in the list,
        # checks if they do exist and appends their values to a string respectively
        return f"[GAP{''.join(f'-{gap_object.get(attr)}' for attr in ['reason', 'unit', 'extent'] if gap_object.get(attr))}]"

    @staticmethod
    def _handle_unclear_and_supplied(gap_object: BeautifulSoup) -> str:
        """Method to handle unclear and supplied tags as GAPs with description and text

        :param gap_object: bs4 object of supplied or unclear tag
        :return: string of the reason, description and text of the given gap_object
        """
        formatted_string = f"[GAP-{gap_object.name}"

        # Add reason and source if available
        for attr in ["reason", "source"]:
            if gap_object.get(attr):
                formatted_string += f"-{gap_object.get(attr)}"

        # Add the length of the text
        formatted_string += f"-{len(gap_object.text.strip())}"

        # Add text
        formatted_string += f"-{gap_object.text.strip()}]"

        return formatted_string

    def _extract_word(self, word_object: BeautifulSoup) -> str:
        """TODO: description

        :param word_object:
        :return:
        """
        # Initialize an empty string to hold the combined text
        combined_text = ""

        # Find all 'abbr' tags and replace them with their respective contents
        abbr_tags_to_replace = word_object.find_all("abbr")
        for tag in abbr_tags_to_replace:
            tag.replace_with(tag.contents[0])

        # Find all 'hi' tags and replace them with their respective contents
        hi_tags_to_replace = word_object.find_all("hi")
        for tag in hi_tags_to_replace:
            tag.replace_with(tag.contents[0])

        if self._clear_only:
            # Iterate over the contents of the <w> tag
            for content in word_object.contents:
                # Check if the content is a string
                if isinstance(content, str):
                    # Append the string to the combined text
                    combined_text += content.strip()
                # Check if the content is an <unclear> tag
                elif content.name in ["unclear", "supplied"]:
                    # Append the representation of the <unclear>/<supplied> tag to the combined text
                    combined_text += self._handle_unclear_and_supplied(content)
        else:
            combined_text += word_object.get_text()

        # replace spaces, tabs and newlines with 'nothing' to concat the different word parts
        return combined_text.replace(" ", "").replace("\t", "").replace("\n", "")

    @staticmethod
    def _decompose_unwanted_tags(
        soup_object: BeautifulSoup, tags_to_decompose: list[str]
    ):
        """Remove unwanted tags from soup object

        :param soup_object: bs4 object containing tags
        :param tags_to_decompose: list of tags to decompose
        :return: cleaned up bs4 object
        """
        for tag_name in tags_to_decompose:
            tags = soup_object.find_all(tag_name)
            for tag in tags:
                tag.decompose()

    def _get_verse_transcription(self, verse_object: BeautifulSoup) -> str:
        """Get the verse transcription of a verse block

        :param verse_object: BeautifulSoup object of ab-tag representing a verse
        """
        verse_transcript = []

        self._decompose_unwanted_tags(verse_object, ["note", "lb", "cb", "fw"])

        # Iterate over all child elements of the div
        for child in verse_object.children:
            if child.name == "w":
                # _extract_word internally handles unclear and supplied tags
                verse_transcript.append(self._extract_word(child))
            elif child.name == "gap":
                verse_transcript.append(self._handle_gap(child))
            else:  # TODO: check if something else is outputted here
                verse_transcript.append(child.getText())

        # remove list entries containing NONE
        verse_transcript = list(filter(None, verse_transcript))
        # Merge all list entries and remove \n and \r etc.
        verse_transcript = " ".join(verse_transcript).strip()
        verse_transcript_clean = re.sub(
            r"\s+", " ", verse_transcript
        )  # Replace multiple spaces with a single space
        return verse_transcript_clean

    def get_transcription_list(self):
        """Get a list of transcriptions from the document

        :return: Updated list of transcriptions
        """
        transcripts = self.transcriptions
        for transcript in transcripts:
            transcript.update(
                {
                    "publisher": self.publisher[0],
                    "source": self.source,
                    "ga": self.ga,
                    "sponsor": " ;".join(list(self.sponsor)),
                    "founder": self.founder,
                    "edition_version": self.edition[0],
                    "edition_date": self.edition[1],
                    "publishing_date": self.publishing_date,
                    "encoding_version": self.encoding_version,
                }
            )
        return transcripts

    def get_manuscript_data(self):
        """Get a dictionary of the manuscript metadata

        :return: dictionary of the manuscript metadata
        """
        manuscript_data = {
            "ga": self.ga,
            "docID": self.alt_identifiers.get("Liste", None),
            "label": self.label,
            "source": self.source,
        }

        return manuscript_data
