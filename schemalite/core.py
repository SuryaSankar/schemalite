import json
from datetime import date, datetime
import dateutil


def instance_of(item, type_):
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
    else:
        return isinstance(item, type_)

def validate_object(schema, data, allow_unknown_fields=None,
                    allow_required_fields_to_be_skipped=None, context=None,
                    polymorphic_identity=None):
    """
        person_schema = {
            "fields": {
                "name": {
                    "required": True
                },
                "gender": {
                    "required": True,
                    "validators": [
                        is_a_type_of(str, unicode),
                        lambda gender, person: (False, "Invalid value")
                        if gender not in ("Male", "Female") else (True, None)
                    ]
                },
                "age": {
                    "validators": [
                        is_a_type_of(int),
                        lambda age, person: (False, "Too old") if age > 40 else (True, None)],
                    "required": lambda person: person.get('gender') == 'Female'
                }
            },
            "allow_unknown_fields": True
        }

        org_schema = {
            "fields": {
                "name": {
                    "required": True
                },
                "ceo": {
                    "target_schema": person_schema,
                    "target_relation_type": "scalar"
                },
                "members": {
                    "target_schema": person_schema,
                    "target_relation_type": "list"
                }
            },
            "validators": [
                lambda org: (False, "Non member cannot be CEO")
                if org["ceo"] not in org["members"] else (True, None)
            ]
        }
    """
    is_valid = True
    errors = None
    if not isinstance(data, dict):
        return (False, {'TYPE_ERROR': "Object is not a dict"})
    if allow_unknown_fields is None:
        allow_unknown_fields = schema.get('allow_unknown_fields', False)
    if allow_required_fields_to_be_skipped is None:
        allow_required_fields_to_be_skipped = schema.get('allow_required_fields_to_be_skipped', False)
    fields = schema.get("fields")
    schema_validators = schema.get("validators", [])
    if fields:
        polymorphic_field = schema.get('polymorphic_on')
        if polymorphic_field:
            if polymorphic_identity is None:
                polymorphic_identity = data.get(polymorphic_field)
            if polymorphic_identity:
                additional_schema_for_polymorph = schema.get("additional_schema_for_polymorphs", {}).get(polymorphic_identity, {})
                for k, v in additional_schema_for_polymorph.get("fields", {}).items():
                    fields[k] = v
                schema_validators += additional_schema_for_polymorph.get("validators", [])
        if not allow_unknown_fields:
            for k in data.keys():
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
            if field_name not in data:
                if allow_required_fields_to_be_skipped:
                    continue
                else:
                    required = field_props.get('required', False)
                    if callable(required):
                        error_message = required.desc or required.__name__
                        required = required(data, schema=schema, context=context)
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
                    allowed = allowed(data, schema=schema, context=context)
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
                                dict_schema = field_props.get('dict_schema')
                                if dict_schema:
                                    validation_result, validation_errors = validate_object(
                                        dict_schema, data[field_name], allow_unknown_fields=allow_unknown_fields,
                                        allow_required_fields_to_be_skipped=allow_required_fields_to_be_skipped,
                                        context=context)
                                    if not validation_result:
                                        field_errors['VALIDATION_ERRORS_FOR_OBJECT'] = validation_errors
                                        field_is_valid = field_is_valid and validation_result
                                        is_valid = is_valid and validation_result
                            elif field_type == list:
                                list_item_type = field_props.get('list_item_type')
                                field_errors['VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST'] = []
                                if type(list_item_type) == type:
                                    if list_item_type == dict:
                                        list_item_schema = field_props.get('list_item_schema')
                                        if list_item_schema:
                                            validation_result, validation_errors = validate_list_of_objects(
                                                list_item_schema, data[field_name], allow_unknown_fields=allow_unknown_fields,
                                                allow_required_fields_to_be_skipped=allow_required_fields_to_be_skipped,
                                                context=context)
                                            if not validation_result:
                                                field_errors['VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST'] = validation_errors
                                                field_is_valid = field_is_valid and validation_result
                                                is_valid = is_valid and validation_result
                                    else:
                                        for item in data[field_name]:
                                            if not instance_of(item, list_item_type):
                                                field_is_valid = False
                                                is_valid = False
                                                field_errors['VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST'].append(
                                                    {"TYPE_ERROR": "Item should be of type {0}".format(list_item_type.__name__)})
                                            else:
                                                field_errors['VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST'].append(None)
                                elif type(list_item_type) == tuple:
                                    for item in data[field_name]:
                                        if not any(instance_of(item, t) for t in list_item_type):
                                            field_is_valid = False
                                            is_valid = False
                                            field_errors['VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST'].append(
                                                {"TYPE_ERROR": "Item should be of type {0}".format(
                                                    "/".join([t.__name__ for t in list_item_type]))})
                                        else:
                                            field_errors['VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST'].append(None)

                                if 'permitted_values_for_list_items' in field_props:
                                    for idx, item in enumerate(data[field_name]):
                                        if item not in field_props['permitted_values_for_list_items']:
                                            if field_errors['VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST'][idx] is None:
                                                field_errors['VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST'][idx] = {}
                                            field_errors['VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST'][idx]['PERMITTED_VALUES_ERROR'] = "Field data can be one of the following only: {0}".format(
                                                "/".join([str(v) for v in field_props['permitted_values_for_list_items']]))
                                            field_is_valid = False
                                            is_valid = False

                            elif not instance_of(data[field_name], field_type):
                                field_errors['TYPE_ERROR'] = "Field data should be of type {0}".format(field_type.__name__)
                                field_is_valid = False
                                is_valid = False
                        elif type(field_type) == tuple:
                            if not any(instance_of(data[field_name], t) for t in field_type):
                                field_errors['TYPE_ERROR'] = "Field data should be of type {0}".format(
                                    "/".join([t.__name__ for t in field_type]))
                                field_is_valid = False
                                is_valid = False

                    if 'permitted_values' in field_props:
                        if data[field_name] not in field_props['permitted_values']:
                            field_errors['PERMITTED_VALUES_ERROR'] = "Field data can be one of the following only: {0}".format(
                                "/".join([v for v in field_props['permitted_values']]))
                            field_is_valid = False
                            is_valid = False

                    for _validator in field_props.get('validators', []):
                        if _validator is None:
                            continue
                        validation_result, validation_errors = _validator(data[field_name], data, schema=schema, context=context)
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
        validation_result, validation_errors = schema_validator(data, schema=schema, context=context)
        if validation_result is False:
            if errors is None:
                errors = {}
            if 'SCHEMA_LEVEL_ERRORS' not in errors:
                errors['SCHEMA_LEVEL_ERRORS'] = []
            errors['SCHEMA_LEVEL_ERRORS'].append(validation_errors)
            is_valid = False

    return (is_valid, errors)


def validate_list_of_objects(schema, datalist, allow_unknown_fields=None, allow_required_fields_to_be_skipped=None, context=None):
    is_valid = True
    errors = []
    if not isinstance(datalist, list):
        return (False, "Expected a list")
    for datum in datalist:
        datum_validity, datum_errors = validate_object(
            schema, datum, allow_unknown_fields=allow_unknown_fields,
            allow_required_fields_to_be_skipped=allow_required_fields_to_be_skipped,
            context=context)
        if datum_validity is False:
            errors.append(datum_errors)
        else:
            errors.append(None)
        is_valid = is_valid and datum_validity
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

## TO BE DEPRECATED ##

from .validators import chained_validator
from .schema_error import SchemaError
from functools import wraps


def raise_(ex):
    raise ex


class Field(object):

    def __init__(self, validator=None, required=True,
                 validator_requires_other_fields=False,
                 internal_name=None, adapter=None):
        self.validator = validator
        self.required = required
        self.validator_requires_other_fields = validator_requires_other_fields
        self.internal_name = internal_name
        self.adapter = adapter

class SchemaObjectField(Field):
    def __init__(self, validator=None, required=True,
                 validator_requires_other_fields=False,
                 internal_name=None, adapter=None, schema=None):
        super(SchemaObjectField, self).__init__(
            validator=validator, required=required,
            validator_requires_other_fields=validator_requires_other_fields,
            internal_name=internal_name, adapter=adapter)
        self.schema = schema

class ListOfSchemaObjectsField(Field):
    def __init__(self, validator=None, required=True,
                 validator_requires_other_fields=False,
                 internal_name=None, adapter=None, schema=None):
        super(ListOfSchemaObjectsField, self).__init__(
            validator=validator, required=required,
            validator_requires_other_fields=validator_requires_other_fields,
            internal_name=internal_name, adapter=adapter)
        self.schema = schema



def chained_adapter(*adapters):
    def _adapter(o):
        res = o
        for a in adapters:
            if a is None:
                continue
            res = a(res)
        return res

    return _adapter


class ValidationResult(object):

    def __init__(self, is_valid, errors):
        self.is_valid = is_valid
        self.errors = errors

    def __nonzero__(self):
        return self.is_valid


class Schema(object):

    @classmethod
    def wrapped_validate(cls, data, envelope_data):
        cls.validate(data)

    @classmethod
    def wrapped_validate_list(cls, data, envelope_data):
        cls.validate_list(data)

    @classmethod
    def validate(cls, data):
        is_valid = True
        errors = None
        attrs_dict = {}
        for klass in cls.__mro__:
            for k, v in klass.__dict__.items():
                if k not in attrs_dict:
                    attrs_dict[k] = v
        for k, attr in attrs_dict.items():
            if isinstance(attr, Field):
                if k not in data:
                    if not isinstance(attr.required, bool):
                        required = attr.required(data)
                    else:
                        required = attr.required
                    if required:
                        is_valid = False
                        if errors is None:
                            errors = {}
                        if 'MISSING_FIELDS' not in errors:
                            errors['MISSING_FIELDS'] = []
                        errors['MISSING_FIELDS'].append(k)
                else:
                    wrapped_validator = None
                    if isinstance(attr, SchemaObjectField):
                        wrapped_validator = attr.schema.wrapped_validate
                    elif isinstance(attr, ListOfSchemaObjectsField):
                        wrapped_validator = attr.schema.wrapped_validate_list
                    if wrapped_validator is not None:
                        if attr.validator is None:
                            attr.validator = wrapped_validator
                        elif isinstance(attr.validator, list):
                            attr.validator.append(wrapped_validator)
                        else:
                            attr.validator = [attr.validator, wrapped_validator]
                    if attr.validator is None:
                        is_valid = is_valid & True
                    else:
                        try:
                            if isinstance(attr.validator, list):
                                for _validator in attr.validator:
                                    if _validator is None:
                                        continue
                                    _validator(data[k], data)
                            else:
                                attr.validator(data[k], data)
                        except SchemaError as e:
                            field_is_valid = False
                            field_errors = e.value
                        else:
                            field_is_valid = True
                            field_errors = None

                        is_valid = is_valid & field_is_valid
                        if not field_is_valid:
                            if errors is None:
                                errors = {}
                            if 'FIELD_LEVEL_ERRORS' not in errors:
                                errors['FIELD_LEVEL_ERRORS'] = {}
                            errors['FIELD_LEVEL_ERRORS'][k] = field_errors
            elif hasattr(attr, 'is_schema_validator'):
                try:
                    attr(data)
                except SchemaError as e:
                    schema_is_valid = False
                    schema_errors = e.value
                else:
                    schema_is_valid = True
                    is_valid = is_valid and schema_is_valid
                if not schema_is_valid:
                    if errors is None:
                        errors = {}
                    if 'SCHEMA_LEVEL_ERRORS' not in errors:
                        errors['SCHEMA_LEVEL_ERRORS'] = {}
                    errors['SCHEMA_LEVEL_ERRORS'][attr.__name__] = schema_errors

        if not is_valid:
            raise SchemaError(errors)

    @classmethod
    def validate_list(cls, datalist):
        is_valid = True
        errors = []
        for datum in datalist:
            try:
                cls.validate(datum)
            except SchemaError as e:
                is_valid = False
                errors.append(e.value)
            else:
                is_valid = is_valid and True
                errors.append(None)
        if not is_valid:
            raise SchemaError(errors)

    @classmethod
    def validator(cls, func):
        cls.schema_validators.append(func)
        return func

    @classmethod
    def adapt(cls, data):
        attrs_dict = {}
        result = {}
        for klass in cls.__mro__:
            for k, v in klass.__dict__.items():
                if k not in attrs_dict:
                    attrs_dict[k] = v
        for k, attr in attrs_dict.items():
            if isinstance(attr, Field) and k in data:
                field_name = attr.internal_name or k
                field_value = data[k]
                if isinstance(attr, SchemaObjectField):
                    attr.adapter = chained_adapter(attr.adapter, attr.schema.adapt)
                elif isinstance(attr, ListOfSchemaObjectsField):
                    attr.adapter = chained_adapter(attr.adapter, attr.schema.adapt_list)
                if attr.adapter is not None:
                    field_value = attr.adapter(field_value)
                result[field_name] = field_value
        return result

    @classmethod
    def adapt_list(cls, datalist):
        return [cls.adapt(datum) for datum in datalist]



def validator(field_name):

    def field_validator_func_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            field = getattr(args[0], field_name)
            if field.validator is None:
                field.validator = func
            elif isinstance(field.validator, list):
                field.validator.append(func)
            else:
                field.validator = [field.validator, func]
            # field.validator = chained_validator(field.validator, func)
            return func(*args, **kwargs)
        return wrapper
    return field_validator_func_wrapper


def schema_validator(func):
    func.is_schema_validator = True
    return func