"""
Fetch lookups at time of docker build
"""
import os
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlretrieve
imd_lookup_url = "https://raw.githubusercontent.com/mysociety/composite_uk_imd/master/composite_lookups/imd_lsoa.json"
region_url = "https://raw.githubusercontent.com/ajparsons/uk_local_authority_names_and_codes/master/uk_local_authorities.csv"
meta_category_url = "https://raw.githubusercontent.com/mysociety/fms_meta_categories/master/full_table.csv"
ruc_url = "https://raw.githubusercontent.com/mysociety/uk_ruc/master/output/composite_ruc.csv"

resources = [imd_lookup_url, region_url, meta_category_url, ruc_url]
dest_dir = Path("resources")


def download_resources():
    """
    download the above files to the local resources directory
    """
    dest_dir.mkdir(exist_ok=True)
    for url in resources:
        filename = (os.path.basename(urlparse(url).path))
        print("fetching {0}".format(filename))
        urlretrieve(url, dest_dir / filename)

if __name__ == "__main__":
    download_resources()
