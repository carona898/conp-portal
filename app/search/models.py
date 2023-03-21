import datetime as dt
from functools import lru_cache
import os
import json
import re

import fnmatch
from typing import Optional

import dateutil
import requests

from app.dats import DATSObject

@lru_cache(maxsize=1)
def _get_latest_test_results(date):
    url = "https://circleci.com/api/v1.1/" \
        + "project/github/CONP-PCNO/conp-dataset/" \
        + "latest/artifacts" \
        + "?branch=master&filter=completed"

    artifacts = requests.get(url).json()

    previous_test_results = {}
    for artifact in artifacts:
        # Merge dictionnaries together.
        previous_test_results = {
            **previous_test_results,
            **requests.get(artifact["url"]).json(),
        }

    return previous_test_results


def get_latest_test_results():
    current_date = dt.datetime.now().astimezone(tz=dateutil.tz.UTC)
    normalized_date = current_date.replace(
        # Round the date to the lowest 4hour
        hour=(current_date.hour // 4 * 4 + 1),
        minute=0,                               # range and give an extra hour gap
        second=0,                               # for tests execution.
        microsecond=0
    )

    return _get_latest_test_results(normalized_date)


class DatasetCache(object):
    def __init__(self, current_app):
        self.current_app = current_app
        dataset_cache_dir = current_app.config['DATASET_CACHE_PATH']
        if not os.path.exists(dataset_cache_dir):
            os.makedirs(dataset_cache_dir)

    @property
    def cachedDatasets(self):
        """
          Return a dict of available cached datasets
        """
        return dict(
            (f.name, f)
            for f in os.scandir(self.current_app.config['DATASET_CACHE_PATH'])
        )

    def getZipLocation(self, dataset):
        """
          1. Server checks if a zip file already exists for this version.
          2. Return zip filepath or None
        """

        datasetmeta = DATSDataset(dataset.fspath)
        zipFilename = datasetmeta.name.replace('/', '__') + '_version-' + \
            datasetmeta.version + '.tar.gz'

        # Look for the filename in the cached datasets
        cached = self.cachedDatasets.get(zipFilename)
        return cached.path if cached is not None else None


class DATSDataset(DATSObject):
    @property
    def schema_org_metadata(self):
        """ Returns json-ld metadata snippet for Google dataset search. """
        try:
            jsonld_obj = {}
            jsonld_obj["@context"] = "https://schema.org/"
            jsonld_obj["@type"] = "Dataset"
            # required fields
            jsonld_obj["name"] = self.descriptor["title"]
            jsonld_obj["description"] = self.descriptor["description"]
            jsonld_obj["version"] = self.descriptor["version"]
            licenses = []
            for license in self.descriptor["licenses"]:
                # license can be of type URL or CreativeWork
                if license["name"].startswith("http"):
                    licenses.append(license["name"])
                else:
                    license_creative_work = {}
                    license_creative_work["@type"] = "CreativeWork"
                    license_creative_work["name"] = license["name"]
                    licenses.append(license_creative_work)
            jsonld_obj["license"] = licenses
            jsonld_obj["keywords"] = [keyword["value"]
                                      for keyword in self.descriptor["keywords"]]
            creators = []
            for creator in self.descriptor["creators"]:
                if "name" in creator:
                    organization = {}
                    organization["@type"] = "Organization"
                    organization["name"] = creator["name"]
                    creators.append(organization)
                else:
                    person = {}
                    person["@type"] = "Person"
                    # all fields below are not required so we have to check if they are present
                    if "firstName" in creator:
                        person["givenName"] = creator["firstName"]
                    if "lastName" in creator:
                        person["familyName"] = creator["lastName"]
                    if "email" in creator:
                        person["email"] = creator["email"]
                    # schema.org requires 'name' or 'url' to be present for Person
                    # dats doesn't have required fields for Person,
                    # therefore in case when no 'fullName' provided or one of 'firstName' or 'lastName' is not provided
                    # we set a placeholder for 'name'
                    if "fullName" in creator:
                        person["name"] = creator["fullName"]
                    elif all(k in creator for k in ("firstName", "lastName")):
                        person["name"] = creator["firstName"] + \
                            " " + creator["lastName"]
                    else:
                        person["name"] = "Name is not provided"
                    # check for person affiliations
                    if "affiliations" in creator:
                        affiliation = []
                        for affiliated_org in creator["affiliations"]:
                            organization = {}
                            organization["@type"] = "Organization"
                            organization["name"] = affiliated_org["name"]
                            affiliation.append(organization)
                        person["affiliation"] = affiliation
                    creators.append(person)
            jsonld_obj["creator"] = creators
            return jsonld_obj

        except Exception:
            return None

    @property
    def status(self):

        test_results = get_latest_test_results()
        tests_status = [
            results["status"]
            for test, results in test_results.items()
            if test.startswith(re.sub("/", "_", self.name) + ":")
        ]

        if tests_status == []:
            # Problem occured during the test suite.
            return "Unknown"
        if any(map(lambda x: x == "Failure", tests_status)):
            return "Broken"
        if all(map(lambda x: x == "Success", tests_status)):
            return "Working"

        return "Unknown"
