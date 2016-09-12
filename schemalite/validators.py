# def type_validator(*types):
#     def validator(o):
#         if any(isinstance(o, _type) for _type in types):
#             return (True, None)
#         return (False, 'TypeMismatch')
#     return validator
from .schema_error import SchemaError


def type_validator(*types):
    def validator(o):
        if not any(isinstance(o, _type) for _type in types):
            raise SchemaError('TypeError')
    return validator

def type_list_validator(*types):
    def validator(olist):
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
        #     return (True, None)
        # else:
        #     return (False, errors)

    return validator


# def chained_validator(*validators):
#     def validator(o):
#         for _validator in validators:
#             if _validator is None:
#                 continue
#             result = _validator(o)
#             if result[0] is False:
#                 return result
#         return (True, None)

#     return validator

def chained_validator(*validators):
    def validator(o):
        for _validator in validators:
            if _validator is None:
                continue
            _validator(o)

    return validator
