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

# Define functions for each task
get_words() {
    echo "Running task: Get words"
    python ./get_words.py
}

parse_tei() {
    echo "Running task: Parse TEI for verses"
    python ./parse_tei.py
}
parse_json() {
    echo "Running task: Parse JSON for manuscript meta data"
    python ./parse_json.py
}
parse_sparql() {
    echo "Running task: Parse sparql for manuscript meta data"
    python ./enhance_sparql.py
}

search_occurrences() {
    echo "Running task: Search occurrences"
    python ./ecm-na28-processing.py
    python ./search_occurrences.py
}

publication_prep() {
    echo "Running task: Publication preparation"
    python ./pub_prep.py
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
1: Get words
2: Parse TEI for manuscript and verse data
3: Parse JSON for manuscript meta data
4: Parse sparql for manuscript meta data
5: Search occurrences
6: Publication preparation 
Input: " user_input

    # Split input into an array
    IFS=',' read -r -a tasks <<< "$user_input"

    # Execute tasks based on user input
    for task in "${tasks[@]}"; do
        case $task in
            1) get_words ;;
            2) parse_tei ;;
            3) parse_json ;;
            4) parse_sparql ;;
            5) search_occurrences ;;
            6) publication_prep ;;
            *) echo "Invalid task: $task" ;;
        esac
    done
fi

# Deactivate the virtual environment
deactivate

echo "Done!"