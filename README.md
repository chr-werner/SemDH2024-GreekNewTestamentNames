# SemDH2024-GreekNewTestamentNames

This repo contains the notebooks used for sourcing data for `A Corpus of Biblical Names in the Greek New Testament to Study the Additions, Omissions, and Variations across Different Manuscripts`, which was submitted to [SemDH 2024: First International Workshop of Semantic Digital Humanities](https://semdh.github.io).

## Structure of this Repository

```text
data/                             General directory for downloaded and generated data
  |-- publish/                    Directory of cleaned up lists
  |   |-- manuscripts.csv
  |   |-- names.csv
  |   |-- occurrences.csv
  |   |-- verses.csv
  |-- tables/                     Directory containing manually curated lists
  |   `-- names.csv               List of manually curated names
  |-- transcriptions/             Directory of transcripts (will be created during download)
  |-- manuscripts/                Directory of manuscript metadata (will be created during download)
  |-- manuscripts.csv             Processed list of manuscripts
  |-- names.csv                   Processed list of names
  |-- occurrences.csv             Processed list of occurrences of names
  `-- verses.csv                  Processed list of verses in manuscripts
notebooks/                        Directory of notebooks used
  |-- 01_download.ipynb           Download files from the IGNTP and NTVMR (TEI files and JSON files)
  |-- 02_get_words.ipynb          Preprocess manual curated list of names for later search
  |-- 03_1_teiparse.ipynb         Parsing TEI files for manuscript metadata and verses
  |-- 03_2_jsonparse.ipynb        Parsing JSON files for manuscript metadata
  |-- 03_3_sparql.ipynb           Enriching manuscript metadata with data from dbpedia
  |-- 04_search.ipynb             Search for occurrences and omissions of names in verses
  |-- 05_pub_prep.ipynb           Clean up processed lists
  |-- constants.py                Constants
  |-- convertes.py                Converter functions
  |-- TEIFile.py                  Class file for TEIFile
  `-- utils.py                    Helper functions
.python-version                   Python version indicator
README                            This README
requirements.txt                  Requirements for Python environment
```

## Install and Use

The recommended Python version for using this repo is `3.9.19`. Dockerimages with Python preinstalled can be found on [Dockerhub](https://hub.docker.com/_/python).

In your Python environment run `pip install -r requirements.txt` from the projects root directory to install [Jupyter](https://jupyter.org). This will enable you to run the notebooks.

The notebooks will automatically download and install the required packages and modules at runtime in their respective kernel.

## SPARQL Queries

We have utilized a SPARQL query for retrieving an initial list of biblical names in the New Testament.

Endpoint: <https://database.factgrid.de/query>

```sparql
SELECT ?Person ?PersonLabel ?noted ?notedLabel ?GenderLabel ?link ?book
WHERE {
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
  
  ?Person wdt:P2 wd:Q8811.
  ?Person wdt:P143 ?noted.
  ?noted wdt:P8 ?book.
  
  FILTER (?book IN (wd:Q74942, wd:Q74943, wd:Q74944, wd:Q74945, wd:Q74946, wd:Q74947, wd:Q74948, wd:Q74949, wd:Q74950, wd:Q74951, wd:Q74952, wd:Q74953, wd:Q74954, wd:Q74955, wd:Q74956, wd:Q74957, wd:Q74958, wd:Q74959, wd:Q74960,  wd:Q74961, wd:Q74962, wd:Q74963, wd:Q74964, wd:Q74965, wd:Q74966, wd:Q74967, wd:Q74968)) 
  
  OPTIONAL { ?Person wdt:P154 ?Gender. }
  OPTIONAL { ?link schema:about ?Person ; schema:isPartOf <https://www.wikidata.org/> . }
}
ORDER BY (?PersonLabel)
```

## Updates and Refinements

There will be/have been updates on this repo. Please have a look the release tags for previous versions.

<!--
## How to Cite

If you use this code or data in your research, please cite:

```bibtex
@Article{Werner2024,
  author       = {Christoph Werner and Zacharias Shoukry and Soham Al-Suadi and Frank Krüger},
  title        = {A Corpus of Biblical Names in the Greek New Testament to Study the Additions, Omissions, and Variations across Different Manuscripts},
  journal      = {tba},
  year         = {2024},
  doi          = {tba},
}
```
-->
