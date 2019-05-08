#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `schemalite` package."""

from __future__ import absolute_import
import pytest


from schemalite import func_and_desc, validate_dict, validate_list_of_dicts
import six
from six.moves import range


person_schema = {
    "fields": {
        "name": {
            "required": True,
            "type": (str, six.text_type)
        },
        "gender": {
            "required": True,
            "type": (str, six.text_type),
            "permitted_values": ("Male", "Female")
        },
        "age": {
            "required": func_and_desc(
                lambda person, **kwargs: person.get('gender') == 'Female',
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
            "permitted_values_for_list_items": list(range(1, 10))
        }
    },
}

org_schema = {
    "fields": {
        "name": {
            "required": True,
            "type": (str, six.text_type)

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


def test_missing_conditionally_required_field():
    female_without_age = {
        "gender": "Female",
        "name": "Sharanya",
    }
    valid, errors = validate_dict(female_without_age, person_schema)
    assert not valid
    assert isinstance(errors, dict)
    assert 'MISSING_FIELDS' in errors
    assert 'age' in errors['MISSING_FIELDS']
    assert 'FIELD_LEVEL_ERRORS' in errors
    assert errors['FIELD_LEVEL_ERRORS']['age']['MISSING_FIELD_ERROR'] == 'Required if gender is female'
