## DEPRECATED ##
from .validators import chained_validator
from functools import wraps
from .schema_error import SchemaError


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
                            attr.validator = [
                                attr.validator, wrapped_validator]
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
                    attr.adapter = chained_adapter(
                        attr.adapter, attr.schema.adapt)
                elif isinstance(attr, ListOfSchemaObjectsField):
                    attr.adapter = chained_adapter(
                        attr.adapter, attr.schema.adapt_list)
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
