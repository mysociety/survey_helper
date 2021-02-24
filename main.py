"""
Flask app to bridge surveygizmo
and other applications
"""
import json
import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote, urlencode

import pandas as pd
import requests
from flask import Flask, request, send_file
from waitress import serve


def str_to_bool(x): return x.lower() == "true"


production_server = str_to_bool(
    os.environ.get("SERVER_PRODUCTION", "false"))

MAPIT_GENERATION = os.environ.get("MAPIT_GENERATION", 41)
MAPIT_API_KEY = os.environ.get("MAPIT_KEY", None)
ACCESS_KEY = os.environ.get("ACCESS_KEY", None)
PORT = int(os.environ.get('PORT', 5000))

postcode_url = "https://mapit.mysociety.org/postcode/{postcode}?generation={generation}"


nice_nation = {"E": "England",
               "S": "Scotland",
               "W": "Wales",
               "N": "Northern Ireland"}


def try_keys(di, *keys):
    for k in keys:
        result = di.get(k, None)
        if result:
            return result


@lru_cache
def imd_lookup():
    with open(Path("resources", "imd_lsoa.json")) as json_file:
        return json.load(json_file)


@lru_cache
def region_lookup():
    df = pd.read_csv(Path("resources", "uk_local_authorities.csv"))
    return df.set_index("local-authority-code")["region"].to_dict()


@lru_cache
def rurality_lookup():
    df = pd.read_csv(Path("resources", "composite_ruc.csv"))
    df["ukruc-3"] = df["ukruc-3"].map({0: "Urban",
                                       1: "Rural",
                                       2: "More rural"})
    return df.set_index("lsoa")["ukruc-3"].to_dict()


@lru_cache
def category_lookup():
    df = pd.read_csv(Path("resources", "full_table.csv"))
    data = {}
    for n, row in df.iterrows():
        data[row[0]] = row[1:]
    return data


def imd_from_lsoa(lsoa):
    """
    from a lsoa, get IMD deciles
    """
    nations = "ESNW"
    imd_data = imd_lookup().get(lsoa, None)
    data = {}
    for n in nations:
        data[n + "_IMD_decile"] = imd_data.get(n + "_d")
    data["UK_IMD_decile"] = imd_data.get("UK_d", "")
    return data


def rural_from_lsoa(lsoa):
    """
    from a lsoa, get UKRUC
    """
    return rurality_lookup().get(lsoa, None)


def region_from_council(code):
    """
    get region from council code
    """
    return region_lookup().get(code, "")


def get_mapit_from_postcode(postcode):
    """
    extract geographic codes from mapit
    """
    headers = {'X-Api-Key': MAPIT_API_KEY}

    r = requests.get(postcode_url.format(
        postcode=quote(postcode), generation=MAPIT_GENERATION), headers=headers)
    mapit_data = r.json()

    wanted_values = {"OLF": "lsoa",
                     "WMC": "parl_con"}

    final = {}

    # if nothing there (bad postcode?), just pass back nothing

    if "areas" not in mapit_data:
        mapit_data["areas"] = {}

    if "shortcuts" not in mapit_data:
        mapit_data["shortcuts"] = {}

    for r in mapit_data["areas"].values():
        if r["type"] in wanted_values:
            code = try_keys(r["codes"], "ons", "gss")
            final[wanted_values[r["type"]]] = code

    if "council" in mapit_data["shortcuts"]:
        area_id = mapit_data["shortcuts"]["council"]
        council = mapit_data["areas"][str(area_id)]
        final["council"] = try_keys(
            council["codes"], "local-authority-canonical", "gss")

    if "lsoa" in final:
        final["nation"] = final["lsoa"][0]
        if final["nation"] == "9":
            final["nation"] = "N"
        final["nation"] = nice_nation[final["nation"]]

    return final


app = Flask(__name__)


@app.route("/")
def home():
    return ("Helper tool for bridging surveygizmo to other databases.")


@app.route("/fms_category", methods=['GET', 'POST'])
def get_category_information():
    # optional basic access requirement
    access_key = request.args.get('access_key', default="", type=str,)
    print(access_key)
    if ACCESS_KEY and access_key != ACCESS_KEY:
        return ("Invalid access key")

    # get postcode from url parameters or form submit
    category = request.args.get('category', default="", type=str,)
    if category == "":
        category = request.form.get('category', default="", type=str,)

    cats = category_lookup().get(
        category, ["Unclassified", "Unclassified", "Unclassified"])
    data = {"cat_a": cats[0], "cat_b": cats[1], "cat_c": cats[2]}

    return urlencode(data)


@app.route("/postcode", methods=['GET', 'POST'])
def get_geo_information():
    """
    View to take a postcode argument and enrich it with geographic information
    """

    # optional basic access requirement
    access_key = request.args.get('access_key', default="", type=str,)
    if ACCESS_KEY and access_key != ACCESS_KEY:
        return ("Invalid access key")

    # get postcode from url parameters or form submit
    postcode = request.args.get('postcode', default="", type=str,)
    if postcode == "":
        postcode = request.form.get('postcode', default="", type=str,)

    if not postcode:
        return ("No valid postcode")
    mapit_data = get_mapit_from_postcode(postcode)

    results = {"blank_value": ""}

    results.update(mapit_data)

    if "lsoa" in results:
        results["ruc"] = rural_from_lsoa(results["lsoa"])
        imd_data = imd_from_lsoa(results["lsoa"])
        results.update(imd_data)

    if "council" in results:
        results["region"] = region_from_council(results["council"])

    return urlencode(results)


if __name__ == "__main__":
    if production_server:
        serve(app, host='0.0.0.0', port=PORT)
    else:
        app.run(host="0.0.0.0", debug=True)
