# -*- coding: utf-8 -*-

"""Top-level package for Schemalite."""

__author__ = """Surya Sankar"""
__email__ = 'suryashankar.m@gmail.com'
__version__ = '0.1.25'

from .core import Schema, Field, validator, schema_validator, SchemaObjectField, ListOfSchemaObjectsField
from .core import validate_object, schema_to_json, func_and_desc
from .schema_error import SchemaError
