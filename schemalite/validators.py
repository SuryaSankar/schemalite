from .core import func_and_desc


def is_a_type_of(*types):
    def validator(o, data, schema, context=None):
        if not any(isinstance(o, _type) for _type in types):
            return (
                False,
                'Object not of type {0}'.format(
                    "/".join([_t.__name__ for _t in types]))
            )
        return (True, None)
    return func_and_desc(
        validator,
        "Should be of type {0}".format("/".join([_t.__name__ for _t in types])))


def is_a_list_of_types_of(*types):
    def validator(olist, data, schema, context=None):
        valid = True
        if not isinstance(olist, list):
            return (False, "Not a list")
        errors = []
        for o in olist:
            if any(isinstance(o, _type) for _type in types):
                valid = valid & True
                errors.append(None)
            else:
                valid = False
                errors.append(
                    'Object not of type {0}'.format(
                        "/".join([_t.__name__ for _t in types]))
                )
        return (valid, errors)
    return func_and_desc(
        validator,
        "Should be a list of objects of type {0}".format("/".join([_t.__name__ for _t in types])))
