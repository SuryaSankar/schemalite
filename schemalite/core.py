import json


def validate_object(schema, data, allow_unknown_fields=None):
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
    fields = schema["fields"]
    if allow_unknown_fields is None:
        allow_unknown_fields = schema.get('allow_unknown_fields', False)
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
        if field_name not in data:
            required = field_props.get('required', False)
            if callable(required):
                required = required(data)
            if required:
                is_valid = False
                if errors is None:
                    errors = {}
                if 'MISSING_FIELDS' not in errors:
                    errors['MISSING_FIELDS'] = []
                errors['MISSING_FIELDS'].append(field_name)
        else:
            field_schema = field_props.get('target_schema')
            field_errors = []
            field_is_valid = True
            if field_schema:
                if field_props.get('target_relation_type') == 'list':
                    validation_result, validation_errors = validate_list_of_objects(
                        field_schema, data[field_name])
                else:
                    validation_result, validation_errors = validate_object(
                        field_schema, data[field_name])
                if not validation_result:
                    field_errors.append(validation_errors)
                    field_is_valid = field_is_valid and validation_result
                    is_valid = is_valid and validation_result

            for _validator in field_props.get('validators', []):
                if _validator is None:
                    continue
                validation_result, validation_errors = _validator(data[field_name], data)
                if not validation_result:
                    field_errors.append(validation_errors)
                    field_is_valid = field_is_valid and validation_result
                    is_valid = is_valid and validation_result

            if not field_is_valid:
                if errors is None:
                    errors = {}
                if 'FIELD_LEVEL_ERRORS' not in errors:
                    errors['FIELD_LEVEL_ERRORS'] = {}
                errors['FIELD_LEVEL_ERRORS'][field_name] = field_errors
    for schema_validator in schema.get("validators", []):
        validation_result, validation_errors = schema_validator(data)
        if validation_result is False:
            if errors is None:
                errors = {}
            if 'SCHEMA_LEVEL_ERRORS' not in errors:
                errors['SCHEMA_LEVEL_ERRORS'] = []
            errors['SCHEMA_LEVEL_ERRORS'].append(validation_errors)
            is_valid = False

    return (is_valid, errors)


def validate_list_of_objects(schema, datalist, allow_unknown_fields=None):
    is_valid = True
    errors = []
    if not isinstance(datalist, list):
        return (False, "Expected a list")
    for datum in datalist:
        datum_validity, datum_errors = validate_object(
            schema, datum, allow_unknown_fields=allow_unknown_fields)
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