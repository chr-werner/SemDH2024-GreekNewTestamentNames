from dataclasses import dataclass
from bs4 import BeautifulSoup
import os
import unicodedata


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
        self.soup = self._read_tei(self.filepath)

    @property
    def ga(self) -> str:
        try:
            return self.soup.find("title", type="document").get("n")
        except Exception as e:
            print(f"{e} for file {self.filepath}")

    @property
    def publisher(self) -> str:
        content = self.soup.find("name", type="org")
        return self._get_elem_text(content)

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
        return self._get_elem_text(content)

    @property
    def sources(self) -> list[Source]:
        sources_in_header = self.soup.find_all("msIdentifier")

        sources = []
        for source in sources_in_header:
            country = self._get_elem_text(source.country)
            settlement = self._get_elem_text(source.settlement)
            repository = self._get_elem_text(source.repository)
            idno = self._get_elem_text(source.idno)

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

            text_reconstructed = self._concat_text_from_tags_2(all_words)
            # remove diacritics from text
            text_reconstructed = self._str_remove_diacritics(text_reconstructed)
            marks = self._get_marks_2(all_words)
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
    def _get_elem_text(elem, default="") -> str:
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

    @staticmethod
    def _concat_text_from_tags_2(tags: list) -> str:
        """concatenate texts of multiple tags to space seperated string

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

            # Filter out text from "note", "lb", "cb" subtags
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

    @staticmethod
    def _replace_characters(tag, mark: str, replacement: str):
        """Helper function to replace characters

        :param tag:
        :param mark:
        :param replacement:
        :return:
        """
        for child in tag.children:
            if child.name == mark:
                child.string = replacement * len(child.text)

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
        ).lower()

    def _get_marks_2(self, tags: list) -> str:
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
            self._replace_characters(tag, "supplied", "s")
            self._replace_characters(tag, "unclear", "u")
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


#    @staticmethod
#    def _concat_text_from_tags(tags: list) -> str:
#        """concatenate texts of multiple tags to space seperated string
#
#        :param tags: list of tags to concatenate text from
#        :return: string of tag texts
#        """
#        words = []
#
#        # Extract text from each 'w' tag and its child elements
#        for tag in tags:
#            # Filter out text from "note", "lb", "cb" subtags
#            text_parts = [
#                part.get_text(separator="", strip=True)
#                for part in tag.contents
#                if part.name not in ["note", "lb", "cb"]
#            ]
#            words.append("".join([item for item in text_parts if item != ""]))
#
#        return " ".join(words)
#
#    @staticmethod
#    def get_marks(tags: list) -> str:
#        """Function to extract weather a tag is supplied or unclear
#
#        :param tags: list of xml tags
#        :return: string of characters in range(c,s,u)
#        """
#        word_marks = []
#        # Replace characters based on conditions
#        for tag in tags:
#            replace_characters(tag, "supplied", "s")
#            replace_characters(tag, "unclear", "u")
#            text = tag.get_text(separator="", strip=True)
#            # replace every char that is not a 'u' or 's' with a 'c'
#            text = "".join(["c" if char not in ["s", "u"] else char for char in text])
#
#            word_marks.append(text)
#
#        return " ".join(word_marks)
