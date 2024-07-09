import pytest
from bs4 import BeautifulSoup
from TEIFile import TEIFile
from utils import (
    generate_transcription_url,
    format_xml,
    bkv_nkv_from_verse_id,
    gap_clean,
)
import pandas as pd
import xml.etree.ElementTree as ET
import re


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        (
            pd.Series({"nkv": "Matt.1.15", "docID": 12345, "source": "ntvmr"}),
            "https://ntvmr.uni-muenster.de/community/vmr/api/transcript/get/?docid=12345&indexContent=Matt.1.15&format=xhtml",
        ),
        (
            pd.Series({"nkv": "Acts.1.14", "docID": 40456, "source": "ntvmr"}),
            "https://ntvmr.uni-muenster.de/community/vmr/api/transcript/get/?docid=40456&indexContent=Acts.1.14&format=xhtml",
        ),
    ],
)
def test_generate_transcription_url(input_value, expected_output):
    assert generate_transcription_url(input_value) == expected_output


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        (
            "<gap reason='unspecified' unit='line' extent='1'/>",
            "[GAP-unspecified-line-1]",
        ),
        ("<gap reason='unspecified'/>", "[GAP-unspecified]"),
        ("<gap reason='lacuna' unit='line' extent='part'/>", "[GAP-lacuna-line-part]"),
        ("<gap reason='lacuna' unit='line' extent='4'/>", "[GAP-lacuna-line-4]"),
        ("<gap reason='lacuna' unit='char' extent='part'/>", "[GAP-lacuna-char-part]"),
        ("<gap reason='lacuna' unit='char' extent='4'/>", "[GAP-lacuna-char-4]"),
        ("<gap reason='lacuna' unit='word' extent='part'/>", "[GAP-lacuna-word-part]"),
        (
            "<gap reason='lacuna' unit='verse' extent='part'/>",
            "[GAP-lacuna-verse-part]",
        ),
        (
            "<gap reason='lacuna' unit='chapter' extent='part'/>",
            "[GAP-lacuna-chapter-part]",
        ),
        ("<gap reason='lacuna' unit='book' extent='part'/>", "[GAP-lacuna-book-part]"),
        ("<gap reason='witnessEnd'/>", "[GAP-witnessEnd]"),
    ],
)
def test_handle_gap(input_value, expected_output):
    # start instance of Class, parameter without any meaning
    obj = TEIFile("../data/transcriptions/test/lectionary.xml", True, True)
    # read test input xml
    soup = BeautifulSoup(input_value, "xml")
    # get gap tag
    tag = soup.find("gap")
    # function test
    assert obj._handle_gap(tag) == expected_output


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        (
            "<w>οχλος<unclear>π</unclear></w>",
            "οχλος[GAP-unclear-1-π]",
        ),
        (
            "<w>ιερου<supplied reason='unspecified'>σο</supplied><unclear>λυ</unclear><supplied reason='unspecified'>μα</supplied></w>",
            "ιερου[GAP-supplied-unspecified-2-σο][GAP-unclear-2-λυ][GAP-supplied-unspecified-2-μα]",
        ),
        (
            "<w><abbr type='nomSac'><supplied reason='unspecified'><hi rend='overline'>ις</hi></supplied></abbr></w>",
            "[GAP-supplied-unspecified-2-ις]",
        ),
        (
            "<w>μα<abbr type='nomSac'><supplied reason='unspecified'><hi rend='overline'>ις</hi></supplied></abbr></w>",
            "μα[GAP-supplied-unspecified-2-ις]",
        ),
        (
            "<w>ευαγγελ<supplied source='na28' reason='illegible'>ιον</supplied></w>",
            "ευαγγελ[GAP-supplied-illegible-na28-3-ιον]",
        ),
    ],
)
def test_extract_word_clearonly(input_value, expected_output):
    # start instance of Class, parameter without any meaning
    obj = TEIFile("../data/transcriptions/test/lectionary.xml", True, True)
    # read test input xml
    soup = BeautifulSoup(input_value, "xml")
    # get gap tag
    tag = soup.find("w")
    # function test
    assert obj._extract_word(tag) == expected_output


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        (
            "<w>οχλος<unclear>π</unclear></w>",
            "οχλοςπ",
        ),
        (
            "<w>ιερου<supplied reason='unspecified'>σο</supplied><unclear>λυ</unclear><supplied reason='unspecified'>μα</supplied></w>",
            "ιερουσολυμα",
        ),
        (
            "<w><abbr type='nomSac'><supplied reason='unspecified'><hi rend='overline'>ις</hi></supplied></abbr></w>",
            "ις",
        ),
        (
            "<w>μα<abbr type='nomSac'><supplied reason='unspecified'><hi rend='overline'>ις</hi></supplied></abbr></w>",
            "μαις",
        ),
        (
            "<w>ευαγγελ<supplied source='na28' reason='illegible'>ιον</supplied></w>",
            "ευαγγελιον",
        ),
    ],
)
def test_extract_word_all(input_value, expected_output):
    # start instance of Class, parameter without any meaning
    obj = TEIFile("../data/transcriptions/test/lectionary.xml", False, True)
    # read test input xml
    soup = BeautifulSoup(input_value, "xml")
    # get gap tag
    tag = soup.find("w")
    # function test
    assert obj._extract_word(tag) == expected_output


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        (
            "<ab n='B04K1V51'><gap reason='lacuna' unit='verse' extent='rest'/><w><abbr type='nomSac'><hi rend='overline'>θυ</hi></abbr></w><w>και</w><w>κα<lb break='no' xml:id='P1rC1L3-L329' n='3'/>ταβαινοντας</w><lb xml:id='P1rC1L4-L329' n='4'/><w>μα<abbr type='nomSac'><supplied reason='unspecified'><hi rend='overline'>ις</hi></supplied></abbr></w><w>του</w><lb xml:id='P1rC1L5-L329' n='5'/><note type='local' xml:id='B04K12V12-P2-2'>Für ιερου(σαλ)ημ ε ist die Luecke zu klein und der Akzent wäre falsch. ιερουσολυμα ist Fehlerlesart.</note></ab>",
            "[GAP-lacuna-verse-rest] θυ και καταβαινοντας μα[GAP-supplied-unspecified-2-ις] του",
        ),
        (
            "<ab n='B04K1V51'><fw type='lectTitle'><w>ευαγγελ<supplied source='na28' reason='illegible'>ιον</supplied></w><w><supplied source='na28' reason='illegible'>κατα</supplied></w><w><supplied source='na28' reason='illegible'>ιωναννην</supplied></w></fw><gap reason='lacuna' unit='verse' extent='rest'/><w><abbr type='nomSac'><hi rend='overline'>θυ</hi></abbr></w><w>και</w><w>κα<lb break='no' xml:id='P1rC1L3-L329' n='3'/>ταβαινοντας</w><lb xml:id='P1rC1L4-L329' n='4'/><w>μα<abbr type='nomSac'><supplied reason='unspecified'><hi rend='overline'>ις</hi></supplied></abbr></w><w>του</w><lb xml:id='P1rC1L5-L329' n='5'/><note type='local' xml:id='B04K12V12-P2-2'>Für ιερου(σαλ)ημ ε ist die Luecke zu klein und der Akzent wäre falsch. ιερουσολυμα ist Fehlerlesart.</note><pc>·</pc></ab>",
            "[GAP-lacuna-verse-rest] θυ και καταβαινοντας μα[GAP-supplied-unspecified-2-ις] του ·",
        ),
        (
            "<ab n='1Cor.11.19'><w>δι</w><w>γ<unclear reason='damage to page'>αρ</unclear></w><w><unclear reason='damage to page'>και</unclear></w><gap reason='lacuna'/> <pb n='4' type='page' xml:id='P4-016'/> <cb n='P4C1-016'/> <lb n='P4C1L-016'/></ab>",
            "δι γ[GAP-unclear-damagetopage-2-αρ] [GAP-unclear-damagetopage-3-και] [GAP-lacuna]",
        ),
    ],
)
def test_get_verse_transcription_clearOnly(input_value, expected_output):
    # start instance of Class, parameter without any meaning
    obj = TEIFile("../data/transcriptions/test/lectionary.xml", True, True)
    # read test input xml
    soup = BeautifulSoup(input_value, "xml")
    # get gap tag
    tag = soup.find("ab")
    # function test
    assert obj._get_verse_transcription(tag) == expected_output


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        (
            "<ab n='B04K1V51'><fw type='lectTitle'><w>ευαγγελ<supplied source='na28' reason='illegible'>ιον</supplied></w><w><supplied source='na28' reason='illegible'>κατα</supplied></w><w><supplied source='na28' reason='illegible'>ιωναννην</supplied></w></fw><gap reason='lacuna' unit='verse' extent='rest'/><w><abbr type='nomSac'><hi rend='overline'>θυ</hi></abbr></w><w>και</w><w>κα<lb break='no' xml:id='P1rC1L3-L329' n='3'/>ταβαινοντας</w><lb xml:id='P1rC1L4-L329' n='4'/><w>μα<abbr type='nomSac'><supplied reason='unspecified'><hi rend='overline'>ις</hi></supplied></abbr></w><w>του</w><lb xml:id='P1rC1L5-L329' n='5'/><note type='local' xml:id='B04K12V12-P2-2'>Für ιερου(σαλ)ημ ε ist die Luecke zu klein und der Akzent wäre falsch. ιερουσολυμα ist Fehlerlesart.</note></ab>",
            "[GAP-lacuna-verse-rest] θυ και καταβαινοντας μαις του",
        ),
        (
            "<ab n='B04K1V51'><fw type='lectTitle'><w>ευαγγελ<supplied source='na28' reason='illegible'>ιον</supplied></w><w><supplied source='na28' reason='illegible'>κατα</supplied></w><w><supplied source='na28' reason='illegible'>ιωναννην</supplied></w></fw><gap reason='lacuna' unit='verse' extent='rest'/><w><abbr type='nomSac'><hi rend='overline'>θυ</hi></abbr></w><w>και</w><w>κα<lb break='no' xml:id='P1rC1L3-L329' n='3'/>ταβαινοντας</w><lb xml:id='P1rC1L4-L329' n='4'/><w>μα<abbr type='nomSac'><supplied reason='unspecified'><hi rend='overline'>ις</hi></supplied></abbr></w><w>του</w><lb xml:id='P1rC1L5-L329' n='5'/><note type='local' xml:id='B04K12V12-P2-2'>Für ιερου(σαλ)ημ ε ist die Luecke zu klein und der Akzent wäre falsch. ιερουσολυμα ist Fehlerlesart.</note><pc>·</pc></ab>",
            "[GAP-lacuna-verse-rest] θυ και καταβαινοντας μαις του ·",
        ),
        (
            "<ab n='1Cor.11.19'><w>δι</w><w>γ<unclear reason='damage to page'>αρ</unclear></w><w><unclear reason='damage to page'>και</unclear></w><gap reason='lacuna'/> <pb n='4' type='page' xml:id='P4-016'/> <cb n='P4C1-016'/> <lb n='P4C1L-016'/></ab>",
            "δι γαρ και [GAP-lacuna]",
        ),
    ],
)
def test_get_verse_transcription_all(input_value, expected_output):
    # start instance of Class, parameter without any meaning
    obj = TEIFile("../data/transcriptions/test/lectionary.xml", False, True)
    # read test input xml
    soup = BeautifulSoup(input_value, "xml")
    # get gap tag
    tag = soup.find("ab")
    # function test
    assert obj._get_verse_transcription(tag) == expected_output


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        (  # ancient greek without scentence marks
            "Χαίρετε ὦ φίλοι Ἐύχομαι ὑμῖν καλὰς ἡμέρας παρεῖναι",
            "χαιρετε ω φιλοι ευχομαι υμιν καλας ημερας παρειναι",
        ),
        (  # English with sentence marks
            "Hello, world!",
            "hello, world!",
        ),
    ],
)
def test_str_remove_diacritics(input_value, expected_output):
    # start instance of Class, parameter without any meaning
    obj = TEIFile("../data/transcriptions/test/lectionary.xml", True, True)
    # function test
    assert obj._str_remove_diacritics(input_value).lower() == expected_output


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        (
            "<div><w>τοις</w><w>ουσιν</w>  <w>εν</w><w>εφεσω</w><w>και</w><w>πι                            <lb n=\"P114vC1L-1\" break='no'/>στοις</w></div>",
            '<div><w>τοις</w><w>ουσιν</w><w>εν</w><w>εφεσω</w><w>και</w><w>πι<lb n="P114vC1L-1" break="no" />στοις</w></div>',
        ),
    ],
)
def test_format_xml(input_value, expected_output):
    root = ET.fromstring(input_value)
    assert format_xml(root) == expected_output


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        (
            pd.DataFrame({"verse": ["B01K1V1"]}),
            pd.DataFrame(
                # the order of nkv and bkv is important
                {"verse": ["B01K1V1"], "nkv": ["Matt.1.1"], "bkv": ["B01K1V1"]}
            ),
        ),
        (
            pd.DataFrame({"verse": ["Matt.1.1"]}),
            pd.DataFrame(
                # the order of nkv and bkv is important
                {"verse": ["Matt.1.1"], "bkv": ["B01K1V1"], "nkv": ["Matt.1.1"]}
            ),
        ),
        (
            pd.DataFrame({"verse": ["B01KInscriptioV0"]}),
            pd.DataFrame(
                # the order of nkv and bkv is important
                {
                    "verse": ["B01KInscriptioV0"],
                    "nkv": ["Matt.Inscriptio"],
                    "bkv": ["B01KInscriptioV0"],
                }
            ),
        ),
        (
            pd.DataFrame({"verse": ["Matt.subscriptio"]}),
            pd.DataFrame(
                # the order of nkv and bkv is important
                {
                    "verse": ["Matt.subscriptio"],
                    "bkv": ["B01KSubscriptioV0"],
                    "nkv": ["Matt.Subscriptio"],
                }
            ),
        ),
    ],
)
def test_verse_id_to_bkv_nkv(input_value, expected_output):
    row1 = input_value.iloc[0]  # read initial dataframe row
    bkv_nkv_from_verse_id(row1)  # update the initial dataframe row
    row2 = expected_output.iloc[0]  # read second (testing) dataframes row
    assert row1.equals(row2) is True  # check rows against each other


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        (  # ancient greek without scentence marks
            "ο εμε μεισων · και τον πατερα μου μισει :",
            "ο εμε μεισων και τον πατερα μου μισει",
        ),
        (  # English with sentence marks
            "hello, world!",
            "hello world",
        ),
    ],
)
def test_str_remove_punctuation(input_value, expected_output):
    assert TEIFile._str_remove_punctuation(input_value) == expected_output


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        (  # ancient greek without scentence marks
            "[GAP-supplied-illegible-na28-1-μ]ακαριοι οι δεδιωγμενοι ενεκεν δικαιοσυνης οτι αυτων εστιν η βασιλεια των ουνων",
            "μακαριοι οι δεδιωγμενοι ενεκεν δικαιοσυνης οτι αυτων εστιν η βασιλεια των ουνων",
        ),
        (  # English with sentence marks
            "[GAP-supplied-illegible-na28-1-μ]ακαριοι [GAP-supplied-illegible-na28-1-μ][GAP-supplied-illegible-na28-1-μ]οι δεδιωγμενοι ενεκεν δικαιοσυνης οτι αυτων εστιν η βασιλεια των ουνων",
            "μακαριοι μμοι δεδιωγμενοι ενεκεν δικαιοσυνης οτι αυτων εστιν η βασιλεια των ουνων",
        ),
    ],
)
def test_gap_clean(input_value, expected_output):
    assert gap_clean(input_value) == expected_output


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        (  # ancient greek without scentence marks
            "[GAP-supplied-illegible-na28-1-μ]ακαριοι οι δεδιωγμενοι ενεκεν δικαιοσυνης οτι αυτων εστιν η βασιλεια των ουνων",
            "μακαριοι οι δεδιωγμενοι ενεκεν δικαιοσυνης οτι αυτων εστιν η βασιλεια των ουνων",
        ),
        (  # English with sentence marks
            "[GAP-supplied-illegible-na28-1-μ]ακαριοι [GAP-supplied-illegible-na28-1-μ][GAP-supplied-illegible-na28-1-μ]οι δεδιωγμενοι ενεκεν δικαιοσυνης οτι αυτων εστιν η βασιλεια των ουνων",
            "μακαριοι μμοι δεδιωγμενοι ενεκεν δικαιοσυνης οτι αυτων εστιν η βασιλεια των ουνων",
        ),
    ],
)
def test_extract_greek_and_spaces(input_value, expected_output):
    s = "".join(re.findall(r"[Α-Ωα-ω\s]+", input_value))
    s = re.sub(r"\s+", " ", s).strip()
    assert s == expected_output
