import glob
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

from constants import (
    ALL,
    ERROR_LOG,
    IGNTP_PATH,
    MAX_WORKERS,
    NTVMR_INDEX_URL,
    NTVMR_PATH,
    OVERWRITE,
)
from tqdm import tqdm
from utils import (
    download_igntp_transcripts,
    download_ntvmr_transcripts,
    fetch_xml,
    get_docID_set,
    get_ga_set,
)

# get docID and GA sets
fetch_xml(NTVMR_INDEX_URL, f"{NTVMR_PATH}/metadata_list.xml", ERROR_LOG)
docID_set = get_docID_set(f"{NTVMR_PATH}/metadata_list.xml", all=ALL)
ga_set = get_ga_set(f"{NTVMR_PATH}/metadata_list.xml", all=ALL)

# Start Downloads
print("Download manuscripts from IGNTP 'API'")
# execute threadpool
with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
    # Submit all tasks and keep track of the futures
    futures = {
        executor.submit(download_igntp_transcripts, ga, ERROR_LOG, OVERWRITE): ga
        for ga in ga_set
    }
    # Use tqdm to show progress
    for future in tqdm(as_completed(futures), total=len(futures)):
        try:
            # Optionally retrieve result or handle it
            future.result()
        except Exception as e:
            # Handle exceptions if needed
            print(f"Exception occurred for {futures[future]}: {e}")
print("Download finished")

# remove basetext files as they are not needed by getting a list of files matching the pattern
files_to_delete = glob.glob(
    os.path.join(IGNTP_PATH, "**", "*basetext*.xml"), recursive=True
)
for file_path in files_to_delete:
    print(f"Delete {file_path}")
    os.remove(file_path)

print("Download manuscripts from NTVMR API:")
# execute threadpool
with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
    # Submit all tasks and keep track of the futures
    futures = {
        executor.submit(
            download_ntvmr_transcripts, docID, NTVMR_PATH, ERROR_LOG, OVERWRITE
        ): docID
        for docID in docID_set
    }
    # Use tqdm to show progress
    for future in tqdm(as_completed(futures), total=len(futures)):
        try:
            # Optionally retrieve result or handle it
            future.result()
        except Exception as e:
            # Handle exceptions if needed
            print(f"Exception occurred for {futures[future]}: {e}")
print("Download finished")
