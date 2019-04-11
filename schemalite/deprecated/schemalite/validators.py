## TO BE DEPRECATED ##
from .schema_error import SchemaError


def type_validator(*types):
    def validator(o, data):
        if not any(isinstance(o, _type) for _type in types):
            raise SchemaError('TypeError')
    return validator


def type_list_validator(*types):
    def validator(olist, data):
        valid = True
        errors = []
        for o in olist:
            if any(isinstance(o, _type) for _type in types):
                valid = valid & True
                errors.append(None)
            else:
                valid = False
                errors.append('TypeError')
        if not valid:
            raise SchemaError(errors)
    return validator


def chained_validator(*validators):
    def validator(o, data):
        for _validator in validators:
            if _validator is None:
                continue
            _validator(o, data)

    return validator
