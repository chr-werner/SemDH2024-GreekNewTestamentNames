from concurrent.futures import ProcessPoolExecutor, as_completed

from tqdm import tqdm
from utils import (
    check_and_create_directory,
    download_ntvmr_manuscripts,
    fetch_xml,
    get_docID_set,
)

NTVMR_INDEX_URL = "https://ntvmr.uni-muenster.de/community/vmr/api/metadata/liste/get/"
NTVMR_PATH = "./ntvmr/"
OVERWRITE = True
ERROR_LOG = "./error.log"
EVERY_MANUSCRIPT = True
MAX_WORKERS = 5

# create directory if needed
check_and_create_directory(NTVMR_PATH)
# get docID and GA sets
fetch_xml(NTVMR_INDEX_URL, NTVMR_PATH + "metadata_list.xml", ERROR_LOG)
docID_set = get_docID_set(NTVMR_PATH + "metadata_list.xml", everything=EVERY_MANUSCRIPT)


# Start Downloads
print("Download manuscript data from NTVMR")
# Execute the download in parallel
with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
    # Submit all tasks and keep track of the futures
    futures = {
        executor.submit(
            download_ntvmr_manuscripts, docID, NTVMR_PATH, ERROR_LOG, overwrite=True
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
