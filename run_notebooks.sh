#!/bin/bash

# Step 1: Check if .venv exists, if not create a virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists."
fi

# Step 2: Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Step 3: Install dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "requirements.txt not found, skipping installation."
fi

# Convert Jupyter notebooks to scripts
jupyter nbconvert --to script --output-dir ./scripts "notebooks/*.ipynb"
cp notebooks/*.py ./scripts
cd scripts

# Replace 'from tqdm.notebook import tqdm' with 'from tqdm import tqdm' in all Python files
find . -type f -name "*.py" -exec sed -i "s/from tqdm\.notebook import tqdm/from tqdm import tqdm/g" {} +
cd ..

# Define functions for each task

get_transcripts() {
    echo "Running task: Get transcripts"
    cd ./nt-transcripts/
    python ./download.py
    cd ..
}

get_manuscripts() {
    echo "Running task: Get manuscripts"
    cd ./nt-manuscripts/
    python ./download.py
    cd ..
}

get_words() {
    echo "Running task: Get words"
    cd scripts
    python ./get_words.py
    cd ..
}

parse_tei() {
    echo "Running task: Parse TEI for verses"
    cd scripts
    python ./parse_tei.py
    cd ..
}
parse_json() {
    echo "Running task: Parse JSON for manuscript meta data"
    cd scripts
    python ./parse_json.py
    cd ..
}
parse_sparql() {
    echo "Running task: Parse sparql for manuscript meta data"
    cd scripts
    python ./enhance_sparql.py
    cd ..
}

search_occurrences() {
    echo "Running task: Search occurrences"
    cd scripts
    python ./ecm-na28-processing.py
    python ./search_occurrences.py
    cd ..
}

publication_prep() {
    echo "Running task: Publication preparation"
    cd scripts
    python ./pub_prep.py
    cd ..
}

# Check if --noninteractive flag is provided
if [[ "$1" == "--noninteractive" ]]; then
    echo "Running in non-interactive mode: executing all tasks..."
    get_words
    parse_tei
    parse_json
    parse_sparql
    search_occurrences
    publication_prep
else
    # Prompt user for input
    read -p "Enter the tasks to run separated by commas: 
1: Get transcripts
2: Get manuscript data
3: Get words
4: Parse TEI for manuscript and verse data
5: Parse JSON for manuscript meta data
6: Parse sparql for manuscript meta data
7: Search occurrences
8: Publication preparation 
Input: " user_input

    # Split input into an array
    IFS=',' read -r -a tasks <<< "$user_input"

    # Execute tasks based on user input
    for task in "${tasks[@]}"; do
        case $task in
            1) get_transcripts ;;
            2) get_manuscripts ;;
            3) get_words ;;
            4) parse_tei ;;
            5) parse_json ;;
            6) parse_sparql ;;
            7) search_occurrences ;;
            8) publication_prep ;;
            *) echo "Invalid task: $task" ;;
        esac
    done
fi

# Deactivate the virtual environment
deactivate

echo "Done!"