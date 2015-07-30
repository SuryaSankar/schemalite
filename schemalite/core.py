from .validators import chained_validator


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
                        errors[k] = 'MissingKey'
                else:
                    if attr.validator is None:
                        is_valid = is_valid & True
                    else:
                        if attr.validator_requires_other_fields:
                            field_is_valid, field_errors = attr.validator(
                                data)
                        else:
                            field_is_valid, field_errors = attr.validator(
                                data[k])
                        is_valid = is_valid & field_is_valid
                        if not field_is_valid:
                            if errors is None:
                                errors = {}
                            errors[k] = field_errors
            elif hasattr(attr, 'is_schema_validator'):
                schema_is_valid, schema_errors = attr(data)
                is_valid = is_valid and schema_is_valid
                if not schema_is_valid:
                    if errors is None:
                        errors = {}
                    errors[attr.__name__] = schema_errors
        return (is_valid, errors)

    @classmethod
    def validate_list(cls, datalist):
        results = [cls.validate(data) for data in datalist]
        return (all(result[0] for result in results),
                [result[1] for result in results])

    @classmethod
    def validator(cls, func):
        cls.schema_validators.append(func)
        return func


def validator(field):
    def field_validator_func_wrapper(func):
        field.validator = chained_validator(field.validator, func)
        return func
    return field_validator_func_wrapper


def schema_validator(func):
    func.is_schema_validator = True
    return func
