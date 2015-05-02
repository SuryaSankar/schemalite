class Field(object):

    def __init__(self, validator=None, required=True):
        self.validator = validator
        self.required = required


class SchemaLite(object):

    def __init__(self, data):
        self.valid = True
        self.errors = {}
        for k, v in self.__class__.__dict__.items():
            if isinstance(v, Field):
                if k not in data:
                    if v.required:
                        self.valid = False
                        self.errors[k] = 'MISSING_KEY'
                else:
                    if v.validator is None:
                        self.valid = self.valid & True
                    else:
                        field_is_valid, field_error = v.validator(data[k])
                        self.valid = self.valid & field_is_valid
                        if not field_is_valid:
                            self.errors[k] = field_error

    def validator(self):
        return (self.valid, self.errors)


def schemalite_validator(SchemaLiteClass):

    def validator(o):
        result = SchemaLiteClass(o)
        return (result.valid, result.errors)

    return validator


def schemalite_list_validator(SchemaLiteClass):

    def validator(olist):
        results = [SchemaLiteClass(o) for o in olist]
        return (all(result.valid for result in results),
                [result.errors for result in results])

    return validator


class SchemaLiteField(Field):

    def __init__(self, schemalite_class, validator=None, required=True):
        if validator is None:
            self.validator = schemalite_validator(schemalite_class)
        else:
            self.validator = lambda val: schemalite_validator(
                schemalite_class)(val) and validator
        self.required = required


class SchemaLiteListField(Field):

    def __init__(self, schemalite_class, validator=None, required=True):
        if validator is None:
            self.validator = schemalite_list_validator(schemalite_class)
        else:
            self.validator = lambda val: schemalite_list_validator(
                schemalite_class)(val) and validator
        self.required = required
