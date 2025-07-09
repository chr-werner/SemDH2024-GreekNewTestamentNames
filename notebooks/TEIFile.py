import copy
import re
import unicodedata

from bs4 import BeautifulSoup
from bs4.element import Tag
from dateutil import parser as dtparser


class TEIFile(object):
    def __init__(self, filepath, clear_only, verbose):
        self._filepath = filepath
        self._soup = self._read_tei(self._filepath)
        if self._soup is None:
            raise ValueError("Failed to parse TEI file")
        self._clear_only = clear_only
        self.verbose = verbose
        self._errors = []

    # All properties below are currently read only
    # to boost performance, we might do not want to parse the whole transcription file,
    # as it can take quiet a while especially for the lectionaries.

    @property
    def ga(self) -> str | None:
        """Property returning the Gregory Aaland (GA) Number

        :return: Gregory Aaland (GA) Number as String
        """
        try:
            if self._soup is None:
                raise ValueError("Soup object is None")
            title_tag = self._soup.find("title", type="document")
            if isinstance(title_tag, Tag):
                n_value = title_tag.get("n")
                return n_value if isinstance(n_value, str) else None
            else:
                raise TypeError("Expected a Tag, got NavigableString or None.")
        except Exception as e:
            self._add_error("No title tag containing the GA number", e)
            return None

    @property
    def publisher(self) -> set[str] | None:
        """Property returning the names of publishing institutions/persons

        :return: set of names of publishing institutions/persons
        """
        publisher_names = set()
        try:
            if self._soup is None:
                raise ValueError("Soup object is None")
            publisher_tag = self._soup.find("publisher")
            if isinstance(publisher_tag, Tag):
                for name_tag in publisher_tag.find_all("name"):
                    publisher_names.add(name_tag.text)
                return publisher_names
            else:
                # publisher_tag is None or NavigableString, so no names to extract
                return None
        except Exception as e:
            self._add_error("No publisher given", e)
            return None

    @property
    def funder(self) -> str | None:
        """Property returning the name of funding institution"""
        try:
            if self._soup is None:
                raise ValueError("Soup object is None")
            funder_tag = self._soup.find("funder")
            if funder_tag is not None:
                return funder_tag.get_text()
            return None
        except Exception as e:
            self._add_error("No funder given", e)
            return None

    @property
    def label(self) -> str | None:
        """Property returning the name of the document"""
        try:
            if self._soup is None:
                raise ValueError("Soup object is None")
            msname_tag = self._soup.find("msName")
            if msname_tag is not None:
                return msname_tag.get_text()
            return None
        except Exception as e:
            self._add_error("No label given", e)
            return None

    @property
    def sponsor(self) -> set[str] | None:
        """Property returning the names of sponsoring institutions/persons"""
        sponsor_names = set()
        try:
            if self._soup is None:
                raise ValueError("Soup object is None")
            sponsor_tag = self._soup.find("sponsor")
            if isinstance(sponsor_tag, Tag):
                for name_tag in sponsor_tag.find_all("name"):
                    sponsor_names.add(name_tag.text)
                return sponsor_names
            else:
                # sponsor tag is None or not a Tag, so no names found
                return None
        except Exception as e:
            self._add_error("No sponsor given", e)
            return None

    @property
    def edition_date(self) -> str | None:
        """Property returning the transcription edition date (in YYYY-MM-DD format)"""

        try:
            if self._soup is None:
                raise ValueError("Soup object is None")
            edition_tag = self._soup.find("edition")
            if not isinstance(edition_tag, Tag):
                raise ValueError("No <edition> tag found")

            date_tag = edition_tag.find("date")
            if not isinstance(date_tag, Tag):
                raise ValueError("No <date> tag found inside <edition>")

            date_str = date_tag.get_text()
            return dtparser.parse(date_str).strftime("%Y-%m-%d")
        except Exception as e:
            self._add_error("No transcription edition date given", e)
            return None

    @property
    def edition_version(self) -> str | None:
        """Property returning the transcription's edition version"""
        try:
            if self._soup is None:
                raise ValueError("Soup object is None")
            edition_tag = self._soup.find("edition")
            if isinstance(edition_tag, Tag):
                n_value = edition_tag.get("n")
                return n_value if isinstance(n_value, str) else None
            return None
        except Exception as e:
            self._add_error("No transcription edition given", e)
            return None

    @property
    def errors(self):
        """Returns the list of errors."""
        return self._errors

    @property
    def publishing_date(self) -> str | None:
        """Property returning the publishing date of the document in YYYY-MM-DD Format

        :return: publishing date of the document
        """
        """Property returning the publishing date of the document in YYYY-MM-DD Format"""
        try:
            if self._soup is None:
                raise ValueError("Soup object is None")
            pub_stmt = self._soup.find("publicationStmt")
            if not isinstance(pub_stmt, Tag):
                raise ValueError("No <publicationStmt> tag found")

            date_tag = pub_stmt.find("date")
            if not isinstance(date_tag, Tag):
                raise ValueError("No <date> tag found inside <publicationStmt>")

            date_str = date_tag.get_text()
            return dtparser.parse(date_str).strftime("%Y-%m-%d")
        except Exception as e:
            self._add_error("No publishing date given", e)
            return None

    @property
    def alt_identifiers(self) -> dict:
        """Property returning alternative identifiers for a document

        TODO: this might be fixed by checking the API endpoint https://ntvmr.uni-muenster.de/community/vmr/api/feature/get/ for further data

        :return: tuples of alternative identifier name and number in this schema
        """
        alt_identifiers = {}
        try:
            if self._soup is None:
                raise ValueError("Soup object is None")
            for alt_identifier in self._soup.find_all("altIdentifier"):
                id_type = alt_identifier.get("type")
                value = alt_identifier.find("idno").getText()
                alt_identifiers[id_type] = value
            return alt_identifiers
        except Exception as e:
            self._add_error("No alternative manuscript identifiers given", e)
            return alt_identifiers

    @property
    def witnesses(self) -> set | None:
        """Property returning the list of witnesses (writers) in the document

        :return: witnesses in the document
        """
        witnesses = set()
        try:
            if self._soup is None:
                raise ValueError("Soup object is None")

            listwit_tag = self._soup.find("listWit")
            if not isinstance(listwit_tag, Tag):
                raise ValueError("No <listWit> tag found")

            for witness in listwit_tag.find_all("witness"):
                wid = witness.get("xml:id")
                if isinstance(wid, str):
                    witnesses.add(wid)

            return witnesses
        except Exception as e:
            self._add_error("No witnesses for the document given", e)
            return None

    @property
    def encoding_version(self) -> str | None:
        """Property returning the encoding version (by the IGNTP) of the document

        :return: encoding version as string
        """
        try:
            if self._soup is None:
                raise ValueError("Soup object is None")

            encoding_desc = self._soup.find("encodingDesc")
            if not isinstance(encoding_desc, Tag):
                raise ValueError("No <encodingDesc> tag found")

            n_value = encoding_desc.get("n")
            return n_value if isinstance(n_value, str) else None

        except Exception as e:
            self._add_error("No transcription encoding version", e)
            return None

    @property
    def revisions(self) -> set | None:
        """Property returning revision history of the document

        :return: list of tuples of revision id, date of the revision and description
        """
        revisions = set()
        try:
            if self._soup is None:
                raise ValueError("Soup object is None")

            revision_desc = self._soup.find("revisionDesc")
            if not isinstance(revision_desc, Tag):
                raise ValueError("No <revisionDesc> tag found")

            for revision in revision_desc.find_all("change"):
                no = revision.get("n")
                date = revision.get("when")
                description = revision.getText()
                revisions.add((no, date, description))
            return revisions
        except Exception as e:
            self._add_error("No revision description of the document", e)
            return None

    @property
    def resp(self) -> tuple | None:
        """Property returning the response object of the document

        :return: triple of lists of creators, transcribers, reconcilers and proofreader
        """
        creators = []
        transcribers = []
        reconcilers = []
        proofreaders = []
        try:
            if self._soup is None:
                raise ValueError("Soup object is None")
            for respStmt in self._soup.find_all("respStmt"):
                resp = respStmt.find("resp").text
                name = respStmt.find("name").text
                # Check the type of responsibility and append to the corresponding list
                if resp == "Created by":
                    creators.append(name)
                elif resp == "Transcribed by" or "Initial transcription by":
                    transcribers.append(name)
                elif resp == "Reconciled by":
                    reconcilers.append(name)
                elif resp == "Proofread by":
                    proofreaders.append(name)
            return creators, transcribers, reconcilers, proofreaders
        except Exception as e:
            self._add_error(
                "No data on creator, transcriber, reconcilers, and/or proofreader", e
            )
            return None

    # @property
    # def lections(self) -> Optional[set]:
    #    """Property returning the set of lections in the document
    #
    #    :return: set of lections in document
    #    """
    #    lections = set()
    #    try:
    #        for lection in self._soup.find_all("div", type="lection"):
    #            # remove all spaces from lection string
    #            lections.add(re.sub(r"\s+", "", lection.get("n")))
    #        return lections
    #    except Exception as e:
    #        self._add_error("No lection data", e)
    #        return None

    # @property
    # def books(self) -> Optional[set]:
    #    """Property returning the set of books in the document
    #
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
    #        self._add_error("No books found", e)
    #        return None

    @property
    def verses(self) -> set | None:
        """Property returning the set of verses in the document

        :return: set of verses in the document
        """
        verses = []
        try:
            if self._soup is None:
                raise ValueError("Soup object is None")
            # Find all <div> elements with type="lection"
            verse_divs = self._soup.find_all("ab", attrs={"n": True})
            # Extract the values of the "n" attribute from each <div> element
            for book in verse_divs:
                verses.append(book.get("n"))
            # Convert the list to a set to remove duplicates
            return set(verses)
        except Exception as e:
            self._add_error("No verses", e)
            return None

    @property
    def nomsac(self) -> list[dict] | None:
        """Property returning the list of nomina sarca and their occurrences in the document

        :return: list of dicts of ga, leaction, verse and nominum sacrum
        """
        nomsac_list = []
        try:
            if self._soup is None:
                raise ValueError("Soup object is None")
            for nom in self._soup.find_all("abbr", type="nomSac"):
                nomsac = nom.getText(strip=True)

                tmp_dict = {
                    "ga": self.ga,
                    "lection": None,
                    "verse": None,
                    "nomSac": nomsac,
                }

                # iterate over parents and get the n attribute (bkv/nkv) from the parent verse and lection
                # break the parenting loop when lection is reached
                for parent in nom.parents:
                    if parent.name == "ab":
                        tmp_dict.update({"verse": parent.attrs["n"]})
                    if "type" in parent.attrs and parent.attrs["type"] == "lection":
                        tmp_dict.update({"lection": parent.attrs["n"]})
                        break
                nomsac_list.append(tmp_dict)
            # Convert the list to a set to remove duplicates
            return nomsac_list

        except Exception as e:
            self._add_error("No nomina sacra found", e)
            return None

    @property
    def transcriptions(self) -> list[dict]:
        # TODO: split into sub functions as currently too much is going on here, also for debugging (see below todos)
        # TODO: test when function is split into sub functions
        """Property returning the transcriptions of verses of the document

        :return: dictionary of the documents structure
        """
        transcriptions_list = []

        # Defensive: ensure verses is iterable, else empty list
        verses = list(self.verses) if self.verses else []

        if self._soup is None:
            self._add_error("Soup object is None", ValueError("Soup object is None"))
            return transcriptions_list  # empty list

        # iterate through all known verse_ids in document
        for idx, verse_id in enumerate(verses, start=1):
            if self.verbose:
                print(f"Verse {idx} of {len(verses)}")

            # find all <ab> tags with attribute n=verse_id
            verse_parts = self._soup.find_all("ab", attrs={"n": verse_id})

            while verse_parts:
                # get first entry
                first_part = verse_parts.pop(0)
                # try to get parent lection
                lection_div = first_part.find_parent("div", {"type": "lection"})

                # if part is a 'I' Part
                if first_part.get("part") == "I" and len(verse_parts) > 0:
                    # TODO: introduce a function here to handle the 'F' part of a verse
                    # also get the followup part ('F')
                    second_part = verse_parts.pop(0)
                    # merge followup into first part
                    first_part.extend(second_part.contents)
                    # TODO: introduce a function here to handle the 'I' and 'F' parts of a word
                    # merge parted words by finding all <w> tags with attribute part='F'
                    part_f_tag = first_part.find("w", attrs={"part": "F"})
                    # check if one is found
                    if part_f_tag:
                        # merge them with previous sibling
                        preceding_w_tag = part_f_tag.find_previous_sibling("w")
                        if preceding_w_tag:
                            # TODO: introduce a function here to combine text of word parts
                            # get text of both word tags
                            combined_text = (
                                preceding_w_tag.get_text() + part_f_tag.get_text()
                            )
                            # create new word tag
                            new_tag = self._soup.new_tag("w", part="combined")
                            new_tag.string = combined_text
                            # Replace the original tags with the new tag
                            preceding_w_tag.insert_after(new_tag)
                            preceding_w_tag.decompose()
                            part_f_tag.decompose()
                    verse_transcripts, verse_texts = self._get_verse_transcription(
                        first_part
                    )

                # else get the transcription of one
                else:
                    verse_transcripts, verse_texts = self._get_verse_transcription(
                        first_part
                    )

                # TODO: test method _create_transcriptions() as a replacement for the below for-loop
                for witness, transcript in verse_transcripts.items():
                    text = self._str_remove_diacritics(
                        verse_texts.get(witness, "")
                    ).lower()
                    transcriptions_list.append(
                        {
                            "lection": lection_div["n"] if lection_div else None,
                            "verse": verse_id,
                            "witness": witness,
                            "transcript": self._str_remove_diacritics(
                                transcript
                            ).lower(),
                            "text": text,
                        }
                    )
                    self._check_for_non_greek(text)
                # self._create_transcriptions(transcriptions_list, verse_transcripts, verse_texts, verse_id, lection_div)

        return transcriptions_list

    def _create_transcriptions(
        self,
        transcriptions_list: list,
        verse_transcripts: dict,
        verse_texts: dict,
        verse_id: str,
        lection_div: str,
    ):
        """TODO: _summary_

        :param list transcriptions_list: _description_
        :param dict verse_transcripts: _description_
        :param dict verse_texts: _description_
        :param str verse_id: _description_
        :param str lection_div: _description_
        """

        for witness, transcript in verse_transcripts.items():
            text = self._str_remove_diacritics(verse_texts.get(witness, "")).lower()
            transcriptions_list.append(
                {
                    "lection": (
                        lection_div.get("n") if isinstance(lection_div, Tag) else None
                    ),
                    "verse": verse_id,
                    "witness": witness,
                    "transcript": self._str_remove_diacritics(transcript).lower(),
                    "text": text,
                }
            )
            self._check_for_non_greek(text)

    @property
    def source(self) -> str | None:
        """Property returning the source of the document

        :return: download source of the document
        """
        if "ntvmr" in str(self._filepath):
            return "ntvmr"
        elif "igntp" in str(self._filepath):
            return "igntp"
        else:
            return None

    def _add_error(self, message, exception):
        self._errors.append({"message": message, "exception": str(exception)})
        # if self.verbose:
        #    print(message, exception)

    def _read_tei(self, tei_file_path: str) -> BeautifulSoup | None:
        """Read a TEI file with beautiful soup

        :param tei_file_path: file path to TEI file
        :return: BeautifulSoup object of TEI file
        """
        try:
            with open(tei_file_path, "r") as tei:
                soup = BeautifulSoup(tei, "xml")
                # Find all tags and remove namespace if present
                for tag in soup.find_all():
                    if ":" in tag.name:
                        tag.name = tag.name.split(":")[-1]
                return soup
        except Exception as e:
            self._add_error("TEI File Parsing Error", e)
            return None

    @staticmethod
    def _str_remove_diacritics(s: str) -> str:
        """Normalize string by removing accents and converting to lower case.

        - unicodedata.normalize('NFKD', s): normalizes the input Unicode string s using NFKD normalization. Valid normalization forms are 'NFC', 'NFKC', 'NFD', and 'NFKD'.
        - (c for c in ...): This is a generator expression that iterates over each character c in the normalized string obtained in the previous step.
        - if unicodedata.category(c) != 'Mn': This condition checks whether the Unicode character c belongs to the
         category 'Mn' (Mark, Non-Spacing). Characters in this category are combining characters that modify the
         meaning of the preceding base character. The condition filters out all combining characters from the
         normalized string.

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
    def _handle_gap(gap_object: Tag) -> str:
        """Function to get information from gap tag

        :param gap_object: bs4 object containing the gap tag
        :return: string of the gap reason and description
        """
        # this oneliner is iterating over the attributes given in the list,
        # checks if they do exist and appends their values to a string respectively
        return f"[GAP{''.join(f'-{gap_object.get(attr)}' for attr in ['reason', 'unit', 'extent'] if gap_object.get(attr))}]"

    @staticmethod
    def _handle_unclear_and_supplied(gap_object: Tag) -> str:
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

    def _extract_word(self, word_object: Tag) -> str:
        """TODO: description

        :param word_object:
        :return:
        """
        # Initialize an empty string to hold the combined text
        combined_text = ""

        if self._clear_only:
            # Iterate over the contents of the <w> tag
            for content in word_object.contents:
                # Check if the content is a string
                if isinstance(content, str):
                    # Append the string to the combined text
                    combined_text += content.strip()
                # Check if the content is an <unclear> tag
                elif isinstance(content, Tag) and content.name in [
                    "unclear",
                    "supplied",
                ]:
                    # Append the representation of the <unclear>/<supplied> tag to the combined text
                    combined_text += self._handle_unclear_and_supplied(content)
        else:
            combined_text += word_object.get_text()

        # replace spaces, tabs and newlines with 'nothing' to concat the different word parts
        return combined_text.replace(" ", "").replace("\t", "").replace("\n", "")

    def _extract_clean_word(self, word_object: Tag) -> str:
        """TODO: description

        :param word_object:
        :return:
        """
        text = word_object.get_text()

        # replace spaces, tabs and newlines with 'nothing' to concat the different word parts
        return text.replace(" ", "").replace("\t", "").replace("\n", "")

    @staticmethod
    def _decompose_tags(soup_object: BeautifulSoup, tags_to_decompose: list[str]):
        """Remove unwanted tags from soup object

        :param soup_object: bs4 object containing tags
        :param tags_to_decompose: list of tag prefixes to decompose
        :return: cleaned up bs4 object
        """
        for tag_name in tags_to_decompose:
            # Use regex to match tags that start with the tag_name
            pattern = re.compile(f"^{re.escape(tag_name)}")
            for tag in soup_object.find_all(pattern):
                tag.decompose()

    @staticmethod
    def _unwrap_tags(soup_object: BeautifulSoup, tags_to_unwrap: list[str]):
        """Remove unwanted tags from soup object

        :param soup_object: bs4 object containing tags
        :param tags_to_decompose: list of tags to decompose
        :return: cleaned up bs4 object
        """
        for tag_name in tags_to_unwrap:
            for tag in soup_object.find_all(tag_name):
                tag.unwrap()

    @staticmethod
    def _get_unique_hands(soup_object: BeautifulSoup) -> set:
        """Checking for all rdg tags and their hand attribute values

        :param soup_object: bs4 object containing tags
        :return: set of hands in the given BeautifulSoup object
        """
        return {rdg.get("hand") for rdg in soup_object.find_all("rdg")}

    @staticmethod
    def _remove_hand(soup_object: BeautifulSoup, hand: str):
        """Remove all hands except the given one from BeautifulSoup object

        :param soup_object: bs4 object containing tags
        :param hand: hand to keep in the BeautifulSoup object
        """
        for app in soup_object.find_all("app"):
            for rdg in app.find_all("rdg"):
                if rdg.get("hand") != hand:
                    rdg.decompose()  # Remove the tag completely

    def _parse_for_words(self, soup_object: BeautifulSoup) -> tuple:
        """Parse the given BeautifulSoup object for word (w) tags and accumulates them in a string

        :param soup_object: bs4 object containing tags
        :return: cleaned up string of words in the given BeautifulSoup object
        """
        # setup word transcript list
        verse_words = []
        verse_words_clean = []

        has_gap = bool(soup_object.find("gap"))
        has_non_selfclosing_w = any(tag.contents for tag in soup_object.find_all("w"))

        # Iterate over all child elements of the div
        # Check if there are any 'w' or 'gap' tags in the soup_object
        if has_non_selfclosing_w or has_gap:
            for child in soup_object.children:
                if isinstance(child, Tag):
                    if child.name == "w":
                        # _extract_word internally handles unclear and supplied tags
                        verse_words.append(self._extract_word(child))
                        # _extract_clean_word only gets the text
                        verse_words_clean.append(self._extract_clean_word(child))
                    elif child.name == "gap":
                        verse_words.append(self._handle_gap(child))
                        verse_words_clean.append(self._extract_clean_word(child))
                    elif child.name in ("supplied", "unclear"):
                        self._add_error(
                            f"Wrong useage of <{child.name}> Tag for a GAP", soup_object
                        )
                    else:
                        self._add_error(
                            f"Unexpected Child Tag ({child.name})", soup_object
                        )
        else:
            # Handle the case where no 'w' or 'gap' tags are found
            self._add_error(f"No 'w' or 'gap' tags found", soup_object)
            # TODO: BUG: there are many occasions, where this error gets thrown (e.g. '<ab n="B03K3V22" osisID="Luke.3.22">και καταβηνα<supplied rend="lacuna">ι το</supplied> πν̅α <unclear>τ</unclear>ο αγ<unclear>ι</unclear><supplied rend="lacuna">ον σωματ</supplied><unclear>ι</unclear><unclear>κ</unclear><unclear>ω</unclear><supplied rend="lacuna">ειδει ως πε</supplied><unclear>ρ</unclear><unclear>ι</unclear><unclear>σ</unclear><supplied rend="lacuna">τεραν</supplied><gap reason=""/></ab>')
            # we might want to do a unclear/supplied handling like:
            #  - get content of ab
            #  - decompose selfclosing w tags
            #  - split by space
            #  - concat unclear/supplied contents per split
            #  - generate GAP tag for those splits (BUT THIS CAN GET REALLY TEDIOUS AS e.g. <supplied rend="lacuna"> IS NOT STANDARD ENCODING)

        # remove list entries containing NONE
        verse_words = list(filter(None, verse_words))
        verse_words_clean = list(filter(None, verse_words_clean))
        # Merge all list entries and remove \n and \r etc.
        verse_transcript = " ".join(verse_words).strip()
        verse_text = " ".join(verse_words_clean).strip()
        # Replace multiple spaces with a single space
        verse_transcript = re.sub(r"\s+", " ", verse_transcript)
        verse_text = re.sub(r"\s+", " ", verse_text)
        # Remove punctuation marks
        verse_text = re.sub(r"[·']", "", verse_text)

        return verse_transcript, verse_text

    def _get_verse_transcription(self, verse_object: BeautifulSoup) -> tuple:
        """Get the verse transcription of a verse block

        1. Tag.decompose() removes a tag from the tree, then completely destroys it and its contents:
            - <lb> (line beginning) marks the beginning of a new (typographic) line in some edition or version of a text
            - <note> (note) contains a note or annotation.
            - <cb> (column beginning) marks the beginning of a new column of a text on a multi-column page.
            - <fw> (forme work) contains a running head (e.g. a header, footer), catchword, or similar material appearing on the current page.
            - <pb> (page beginning) marks the beginning of a new page in a paginated document.
            - <pc> punctuation
            - <num> enumerations
            - <space> extra wide spaces
        2. Tag.unwrap()  replaces a tag with whatever's inside that tag. It's good for stripping out markup:
            - <seg> (arbitrary segment) represents any segmentation of text below the 'chunk' level.
            - <surplus> (surplus) marks text present in the source which the editor believes to be superfluous or redundant.
            - <hi> highlights by e.g. overline
            - <abbr> abbreviations e.g. nomen sacrum
            - <ex>

        :param verse_object: BeautifulSoup object of ab-tag representing a verse
        :return: tuple of transcription
        """
        witness_transcripts = {}
        witness_texts = {}

        # remove unwanted tags including their childs and content
        self._decompose_tags(
            verse_object, ["note", "lb", "cb", "fw", "pb", "pc", "num", "space"]
        )
        # remove tags but keep their childs and content
        self._unwrap_tags(verse_object, ["seg", "surplus", "hi", "abbr", "ex"])
        # get unique witness names from rdg tags
        unique_hands = self._get_unique_hands(verse_object)

        if unique_hands:
            # Create a copy of the soup for each hand and remove irrelevant <rdg> tags
            for hand in unique_hands:
                # Create a copy of the original soup
                soup_copy = copy.deepcopy(verse_object)

                # Remove all <rdg> tags with a different 'hand' value from soup_copy
                self._remove_hand(soup_copy, hand)

                # unwrap agg and rdg tags as we do only have one witness now per parsing
                # <app> (apparatus entry) contains one entry in a critical apparatus, with an optional lemma and usually one or more readings or notes on the relevant passage.
                # <rdg> (reading) contains a single reading within a textual variation (in our case it is a child of app).
                self._unwrap_tags(soup_copy, ["app", "rdg"])

                # parse transcript sentence and add to witnesses list
                witness_transcripts[hand], witness_texts[hand] = self._parse_for_words(
                    soup_copy
                )
        else:
            # parse transcript sentence and add to witnesses list
            witness_transcripts["firsthand"], witness_texts["firsthand"] = (
                self._parse_for_words(verse_object)
            )

        return witness_transcripts, witness_texts

    def _check_for_non_greek(self, string: str):
        """Check for non-Greek characters and return their positions. If non-Greek characters are found, an error is added.

        :param str string: string to check
        """
        greek_pattern = re.compile(
            r"[^α-ωΑ-Ωϛϙϡ\s]"
        )  # Matches any non-Greek character; ϛ (stigma), ϙ (koppa), ϡ (sampi) are archaic letters for 6, 90, 900
        non_greek_positions = [
            (i, char) for i, char in enumerate(string) if greek_pattern.match(char)
        ]

        if non_greek_positions:
            self._add_error(
                "Non-Greek characters found",
                f"Text: {string} Positions: {non_greek_positions}",
            )

    def get_transcription_list(self):
        """Get a list of transcriptions from the document

        :return: Updated list of transcriptions
        """
        # TODO: check if both transcript dicts are identical
        transcripts = self.transcriptions

        for transcript in transcripts:
            transcript.update(
                {
                    "publisher": (
                        " ;".join(list(self.publisher)) if self.publisher else ""
                    ),
                    "source": self.source,
                    "ga": self.ga,
                    "sponsor": " ;".join(list(self.sponsor)) if self.sponsor else "",
                    "funder": self.funder,
                    "edition_version": self.edition_version,
                    "edition_date": self.edition_date,
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
            "docID": (
                self.alt_identifiers.get("Liste") if self.alt_identifiers else None
            ),
            "label": self.label,
            "source": self.source,
        }

        return manuscript_data

    def get_error_data(self) -> dict | None:
        if self.errors:
            return {"file": self._filepath, "errors": self.errors}
