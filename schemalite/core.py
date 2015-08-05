from .validators import chained_validator
from .schema_error import SchemaError
from functools import wraps


def raise_(ex):
    raise ex


class Field(object):

    def __init__(self, validator=None, required=True,
                 validator_requires_other_fields=False):
        self.validator = validator
        self.required = required
        self.validator_requires_other_fields = validator_requires_other_fields


class ValidationResult(object):

    def __init__(self, is_valid, errors):
        self.is_valid = is_valid
        self.errors = errors

    def __nonzero__(self):
        return self.is_valid


class Schema(object):

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
                    if attr.required:
                        is_valid = False
                        if errors is None:
                            errors = {}
                            if '_missing_keys_' not in errors:
                                errors['_missing_keys_'] = []
                        errors['_missing_keys_'].append(k)
                else:
                    if attr.validator is None:
                        is_valid = is_valid & True
                    else:
                        if attr.validator_requires_other_fields:
                            params = data
                        else:
                            params = data[k]
                        try:
                            attr.validator(params)
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
                            errors[k] = field_errors

                        # if attr.validator_requires_other_fields:
                        #     field_is_valid, field_errors = attr.validator(
                        #         data)
                        # else:
                        #     field_is_valid, field_errors = attr.validator(
                        #         data[k])
                        # is_valid = is_valid & field_is_valid
                        # if not field_is_valid:
                        #     if errors is None:
                        #         errors = {}
                        #     errors[k] = field_errors
            elif hasattr(attr, 'is_schema_validator'):
                try:
                    attr(data)
                except SchemaError as e:
                    schema_is_valid = False
                    schema_errors = e.value
                else:
                    schema_is_valid = True
                    is_valid = is_valid and schema_is_valid
                # schema_is_valid, schema_errors = attr(data)
                # is_valid = is_valid and schema_is_valid
                if not schema_is_valid:
                    if errors is None:
                        errors = {}
                    errors[attr.__name__] = schema_errors
        # return (is_valid, errors)

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
        # results = [cls.validate(data) for data in datalist]
        # return (all(result[0] for result in results),
        #         [result[1] for result in results])

    @classmethod
    def validator(cls, func):
        cls.schema_validators.append(func)
        return func


def validator(field_name):

    def field_validator_func_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            field = getattr(args[0], field_name)
            field.validator = chained_validator(field.validator, func)
            return func(*args, **kwargs)
        return wrapper
    return field_validator_func_wrapper


def schema_validator(func):
    func.is_schema_validator = True
    return func
