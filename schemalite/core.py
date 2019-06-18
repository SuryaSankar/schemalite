# -*- coding: utf-8 -*-

"""Main module."""

import json
from datetime import date, datetime
import dateutil
from toolspy import is_int, is_number
from decimal import Decimal


def instance_of(item, type_):
    """This method is an enhanced version of isinstance

    It can handle cases where a number like string is meant
    to be treated as a number or where a datetime like string
    is meant to be treated as a datetime
    """
    if type_ == datetime:
        if isinstance(item, datetime):
            return True
        elif isinstance(item, str) or isinstance(item, unicode):
            return isinstance(dateutil.parser.parse(item), datetime)
        else:
            return False
    elif type_ == date:
        if isinstance(item, date):
            return True
        elif isinstance(item, str) or isinstance(item, unicode):
            return isinstance(dateutil.parser.parse(item), datetime)
        else:
            return False
    elif type_ == int:
        if isinstance(item, int):
            return True
        else:
            return is_int(item)
    elif type_ == float:
        return isinstance(item, float) or is_number(item)
    elif type_ == Decimal:
        return isinstance(item, Decimal) or is_number(item)
    else:
        return isinstance(item, type_)


def validate_schema(schema):
    conditions = [
        isinstance(schema, dict),

    ]
    fields_dict_schema = {
        "validators": [],
        "allow_unknown_fields": True,
    }
    schema_of_schema = {
        "fields": {
            "fields": {
                "required": False,
                "type": dict,
                "dict_schema": fields_dict_schema
            },
            "validators": {
                "type": list,
                "list_item_type": callable,
                "required": False
            },
            "polymorphic_on": {
                "required": False
            }
        },
        "validators": [],
        "wildcard_field_validators": []
    }


def validate_dict(
        dictionary, schema, allow_unknown_fields=None,
        allow_required_fields_to_be_skipped=None,
        polymorphic_identity=None,
        context=None, parent_contexts=None,
        siblings_list=None, curr_obj_idx_in_siblings_list=None,
        schemas_registry=None):
    """The main method to be used to validate a dictionary against a schema

    This method accepts the dictionary to be validated as the first argument and validates
    it against the schema which is passed as the second argument

    Parameters
    -----------

    dictionary: dict
        The dict object which is to be validated

    schema: dict
        The schema against which the validation has to be done.

    allow_unknown_fields: bool
        If this is set to True, the validator will allow the dictionary to have fields which are not specified in the schema.
        The validation will be done only on those fields whose behavior is specified by the schema. The rest would be ignored.

    allow_required_fields_to_be_skipped: bool
        Sometimes even if a field is marked as required, it might become necessary to skip that check when
        the validator is called in certain contexts (Consider POST vs PUT for example. A field might be
        required for the POST request, but might be optional for the PUT request. If you are re-using the
        same validation logic for both, it will be convenient if you can allow the PUT request to allow
        the required fields to be skipped)

        

    Returns
    --------

    validation_status: bool
        A boolean flag which says if the validation succeeded or failed

    validation_errors: dict or str or None
        The errors if any, outputted as a string or a dict based on the schema

    """
    is_valid = True
    errors = None
    if not isinstance(dictionary, dict):
        return (False, {'TYPE_ERROR': "Object is not a dict"})
    if allow_unknown_fields is None:
        allow_unknown_fields = schema.get('allow_unknown_fields', False)
    if allow_required_fields_to_be_skipped is None:
        allow_required_fields_to_be_skipped = schema.get(
            'allow_required_fields_to_be_skipped', False)
    fields = schema.get("fields")
    schema_validators = schema.get("validators", [])
    if fields:
        polymorphic_field = schema.get('polymorphic_on')
        if polymorphic_field:
            if polymorphic_identity is None:
                polymorphic_identity = dictionary.get(polymorphic_field)
            if polymorphic_identity:
                additional_schema_for_polymorph = schema.get(
                    "additional_schema_for_polymorphs", {}).get(polymorphic_identity, {})
                for k, v in additional_schema_for_polymorph.get("fields", {}).items():
                    fields[k] = v
                schema_validators += additional_schema_for_polymorph.get(
                    "validators", [])
        if not allow_unknown_fields:
            for k in dictionary.keys():
                if k not in fields.keys():
                    if errors is None:
                        errors = {}
                    is_valid = False
                    if 'UNKNOWN_FIELDS' not in errors:
                        errors['UNKNOWN_FIELDS'] = []
                    errors['UNKNOWN_FIELDS'].append(k)
        for field_name, field_props in fields.items():
            field_errors = {}
            field_is_valid = True
            if field_name not in dictionary:
                if allow_required_fields_to_be_skipped:
                    continue
                else:
                    required = field_props.get('required', False)
                    if callable(required):
                        error_message = required.desc or required.__name__
                        required = required(
                            dictionary, schema=schema, context=context,
                            parent_contexts=parent_contexts,
                            siblings_list=siblings_list,
                            curr_obj_idx_in_siblings_list=curr_obj_idx_in_siblings_list)
                    else:
                        error_message = '%s is a required field' % field_name
                    if required:
                        is_valid = False
                        field_is_valid = False
                        if errors is None:
                            errors = {}
                        if 'MISSING_FIELDS' not in errors:
                            errors['MISSING_FIELDS'] = []
                        errors['MISSING_FIELDS'].append(field_name)
                        field_errors['MISSING_FIELD_ERROR'] = error_message
            else:
                allowed = field_props.get("allowed", True)
                if callable(allowed):
                    error_message = allowed.desc or allowed.__name__
                    allowed = allowed(
                        dictionary, schema=schema, context=context,
                        parent_contexts=parent_contexts,
                        siblings_list=siblings_list,
                        curr_obj_idx_in_siblings_list=curr_obj_idx_in_siblings_list)
                else:
                    error_message = '%s is not an allowed field' % field_name
                if allowed == False:
                    is_valid = False
                    field_is_valid = False
                    field_errors['FIELD_NOT_ALLOWED_ERROR'] = error_message
                else:
                    field_type = field_props.get('type')
                    if field_type is not None:
                        if type(field_type) == type:
                            if field_type == dict:
                                is_mapped_collection = field_props.get(
                                    'is_mapped_collection')
                                dict_schema = field_props.get('dict_schema')
                                if is_mapped_collection:
                                    pass
                                else:
                                    if dict_schema is None:
                                        rel_schema_cls_name = field_props.get(
                                            'is_a_relation_to')
                                        if rel_schema_cls_name and schemas_registry:
                                            dict_schema = schemas_registry.get(
                                                rel_schema_cls_name)
                                    if dict_schema:
                                        if isinstance(parent_contexts, list):
                                            _parent_contexts = parent_contexts[:]
                                            _parent_contexts.append(context)
                                        else:
                                            _parent_contexts = [context]
                                        validation_result, validation_errors = validate_dict(
                                            dictionary[field_name], schema=dict_schema, allow_unknown_fields=allow_unknown_fields,
                                            allow_required_fields_to_be_skipped=allow_required_fields_to_be_skipped,
                                            parent_contexts=_parent_contexts)
                                        if not validation_result:
                                            field_errors['VALIDATION_ERRORS_FOR_OBJECT'] = validation_errors
                                            field_is_valid = field_is_valid and validation_result
                                            is_valid = is_valid and validation_result
                            elif field_type == list:
                                list_item_type = field_props.get(
                                    'list_item_type')
                                field_errors['VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST'] = [
                                ]
                                if dictionary[field_name] is not None:
                                    if type(list_item_type) == type:
                                        if list_item_type == dict:
                                            list_item_schema = field_props.get(
                                                'list_item_schema')
                                            if list_item_schema is None:
                                                rel_schema_cls_name = field_props.get(
                                                    'is_a_relation_to')
                                                if rel_schema_cls_name is not None and schemas_registry is not None:
                                                    list_item_schema = schemas_registry.get(
                                                        rel_schema_cls_name.__name__)
                                            if list_item_schema:
                                                if isinstance(parent_contexts, list):
                                                    _parent_contexts = parent_contexts[:]
                                                    _parent_contexts.append(
                                                        context)
                                                else:
                                                    _parent_contexts = [
                                                        context]
                                                validation_result, validation_errors = validate_list_of_dicts(
                                                    dictionary[field_name], list_item_schema,
                                                    allow_unknown_fields=allow_unknown_fields,
                                                    allow_required_fields_to_be_skipped=allow_required_fields_to_be_skipped,
                                                    parent_contexts=_parent_contexts)
                                                if not validation_result:
                                                    field_errors['VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST'] = validation_errors
                                                    field_is_valid = field_is_valid and validation_result
                                                    is_valid = is_valid and validation_result
                                        else:
                                            for item in dictionary[field_name]:
                                                if not instance_of(item, list_item_type):
                                                    field_is_valid = False
                                                    is_valid = False
                                                    field_errors['VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST'].append(
                                                        {"TYPE_ERROR": "Item should be of type {0}".format(list_item_type.__name__)})
                                                else:
                                                    field_errors['VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST'].append(
                                                        None)
                                    elif type(list_item_type) == tuple:
                                        for item in dictionary[field_name]:
                                            if not any(instance_of(item, t) for t in list_item_type):
                                                field_is_valid = False
                                                is_valid = False
                                                field_errors['VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST'].append(
                                                    {"TYPE_ERROR": "Item should be of type {0}".format(
                                                        "/".join([t.__name__ for t in list_item_type]))})
                                            else:
                                                field_errors['VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST'].append(
                                                    None)

                                if 'permitted_values_for_list_items' in field_props:
                                    for idx, item in enumerate(dictionary[field_name]):
                                        if item not in field_props['permitted_values_for_list_items']:
                                            if field_errors['VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST'][idx] is None:
                                                field_errors['VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST'][idx] = {
                                                }
                                            field_errors['VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST'][idx]['PERMITTED_VALUES_ERROR'] = "Field data can be one of the following only: {0}".format(
                                                "/".join([str(v) for v in field_props['permitted_values_for_list_items']]))
                                            field_is_valid = False
                                            is_valid = False

                            elif not instance_of(dictionary[field_name], field_type):
                                field_errors['TYPE_ERROR'] = "Field data should be of type {0}".format(
                                    field_type.__name__)
                                field_is_valid = False
                                is_valid = False
                        elif type(field_type) == tuple:
                            if not any(instance_of(dictionary[field_name], t) for t in field_type):
                                field_errors['TYPE_ERROR'] = "Field data should be of type {0}".format(
                                    "/".join([t.__name__ for t in field_type]))
                                field_is_valid = False
                                is_valid = False

                    if 'permitted_values' in field_props:
                        if dictionary[field_name] not in field_props['permitted_values']:
                            field_errors['PERMITTED_VALUES_ERROR'] = "Field data can be one of the following only: {0}".format(
                                "/".join([v for v in field_props['permitted_values']]))
                            field_is_valid = False
                            is_valid = False

                    for _validator in field_props.get('validators', []):
                        if _validator is None:
                            continue
                        validation_result, validation_errors = _validator(
                            dictionary[field_name], dictionary, schema=schema, context=context,
                            parent_contexts=parent_contexts,
                            siblings_list=siblings_list,
                            curr_obj_idx_in_siblings_list=curr_obj_idx_in_siblings_list)
                        if not validation_result:
                            validator_name = _validator.desc.upper() or _validator.__name__.upper()
                            validator_name = validator_name.replace(" ", "_")
                            field_errors[validator_name] = validation_errors
                            field_is_valid = field_is_valid and validation_result
                            is_valid = is_valid and validation_result

            if not field_is_valid:
                if errors is None:
                    errors = {}
                if 'FIELD_LEVEL_ERRORS' not in errors:
                    errors['FIELD_LEVEL_ERRORS'] = {}
                errors['FIELD_LEVEL_ERRORS'][field_name] = field_errors
    for schema_validator in schema_validators:
        validation_result, validation_errors = schema_validator(
            dictionary, schema=schema, context=context, siblings_list=siblings_list,
            parent_contexts=parent_contexts,
            curr_obj_idx_in_siblings_list=curr_obj_idx_in_siblings_list)
        if validation_result is False:
            if errors is None:
                errors = {}
            if 'SCHEMA_LEVEL_ERRORS' not in errors:
                errors['SCHEMA_LEVEL_ERRORS'] = []
            errors['SCHEMA_LEVEL_ERRORS'].append(validation_errors)
            is_valid = False

    return (is_valid, errors)


def validate_list_of_dicts(
        list_of_dicts, dict_schema,
        allow_unknown_fields=None, allow_required_fields_to_be_skipped=None,
        context=None, parent_contexts=None, schemas_registry=None):
    is_valid = True
    errors = []
    if not isinstance(list_of_dicts, list):
        return (False, "Expected a list")
    for idx, dictionary in enumerate(list_of_dicts):
        dictionary_validity, dictionary_errors = validate_dict(
            dictionary, dict_schema, allow_unknown_fields=allow_unknown_fields,
            allow_required_fields_to_be_skipped=allow_required_fields_to_be_skipped,
            context=context, siblings_list=list_of_dicts, parent_contexts=parent_contexts,
            schemas_registry=schemas_registry, curr_obj_idx_in_siblings_list=idx)
        if dictionary_validity is False:
            errors.append(dictionary_errors)
        else:
            errors.append(None)
        is_valid = is_valid and dictionary_validity
    return (is_valid, errors)


def func_and_desc(func, desc):
    func.desc = desc
    return func


def json_encoder(obj):
    if callable(obj):
        if hasattr(obj, 'desc'):
            return obj.desc
        if obj.__name__ == '<lambda>':
            return "Nameless function"
        return obj.__name__
    else:
        try:
            return json.JSONEncoder().default(obj)
        except:
            return unicode(obj)


def schema_to_json(schema):
    return json.dumps(
        schema,
        default=json_encoder)
