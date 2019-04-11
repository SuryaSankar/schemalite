#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `schemalite` package."""

import pytest


from schemalite import func_and_desc


person_schema = {
    "fields": {
        "name": {
            "required": True,
            "type": (str, unicode)
        },
        "gender": {
            "required": True,
            "type": (str, unicode),
            "permitted_values": ("Male", "Female")
        },
        "age": {
            "required": func_and_desc(
                lambda person, **kwargs: person.get('gender')=='Female',
                "Required if gender is female"),
            "type": int,
            "validators": [
                func_and_desc(
                    lambda age, person, **kwargs: (False, "Too old")
                    if age > 40 else (True, None),
                    "Has to be less than 40")
            ]
        },
        "access_levels": {
            "type": list,
            "list_item_type": int,
            "permitted_values_for_list_items": range(1, 10)
        }
    },
}

org_schema = {
    "fields": {
        "name": {
            "required": True,
            "type": (str, unicode)

        },
        "ceo": {
            "required": True,
            "type": dict,
            "dict_schema": person_schema
        },
        "members": {
            "required": True,
            "type": list,
            "list_item_type": dict,
            "list_item_schema": person_schema
        }
    },
    "validators": [
        func_and_desc(
            lambda org, **kwargs: (False, "Non member cannot be CEO")
            if org.get("ceo") not in org.get("members") else (True, None),
            "Non member cannot be CEO")
    ],
    "allow_unknown_fields": True
}



@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string
