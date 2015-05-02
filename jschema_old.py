def return_true_always(value):
    return True


def mark_as_invalid_value(value):
    return "Invalid Value"


class JSchema(object):

    """
    Used to model a JSON object.
    """

    def __init__(self, *args):
        self.fields = []
        for arg in args:
            if isinstance(arg, dict):
                self.fields.append({
                    'key': arg['key'],
                    'validator': arg.get('validator', return_true_always),
                    'required': arg.get('required', True),
                    'error_message': arg.get(
                        'error_message', mark_as_invalid_value)
                })
            else:
                self.fields.append({
                    'key': arg,
                    'validator': return_true_always,
                    'required': True,
                    'error_message': mark_as_invalid_value
                })

    def validates(self, data):
        for field in self.fields:
            key = field['key']
            if key in data:
                if not field['validator'](data[key]):
                    return False
            else:
                if field['required']:
                    return False
        return True

    def validation_errors(self, data):
        error_messages = {}
        for field in self.fields:
            key = field['key']
            if key in data:
                if not field['validator'](data[key]):
                    error_messages[key] = field['error_message'](data[key])
            else:
                if field['required']:
                    error_messages[key] = "Missing Required Field"
        return error_messages


class UserSchema(JSchema):

    name = field(validator=lambda x: x is not None)
    address = field(required=False, validator=AddressSchema.validates)
    customers = field(validator=lambda clist: all(CustomerSchema.validates(c) for c in clist))


UserSchema.validates(data)
UserSchema.validation_errors(data)

validated_user = UserSchema(data)
validated_user.valid
validated_user.errors