from schemalite import Schema, Field, validator
from schemalite.validators import type_validator


class PersonSchema(Schema):

    name = Field(validator=lambda val:
                 (False, 'NULLVALUE') if val is None else (True, None))
    gender = Field(validator=lambda val:
                   (True, None) if val in ['M', 'F']
                   else (False, 'INVALID_VALUE'))
    age = Field(validator=type_validator(int), required=False)

    @validator(age)
    def validate_age(val):
        if 0 < val < 120:
            return (True, None)
        return (False, 'Invalid Value For Age')


class OrganizationSchema(Schema):

    name = Field(validator=lambda val:
                 (False, 'NULLVALUE') if val is None else (True, None))
    head = Field(validator=PersonSchema.validate, required=False)
    members = Field(validator=PersonSchema.validate_list)


if __name__ == '__main__':
    ricky = {'name': 'Ricky', 'gender': 'M'}

    is_valid, errors = PersonSchema.validate(ricky)
    print is_valid
    print errors

    adam = {'name': 'Adam', 'gender': 'M', 'age': -1.4}

    is_valid, errors = PersonSchema.validate(adam)
    print is_valid
    print errors

    john = {'name': 'John', 'gender': 'M', 'age': 200}

    is_valid, errors = PersonSchema.validate(john)
    print is_valid
    print errors

    maya = {'name': 'Maya', 'gender': 'M', 'age': 20}

    is_valid, errors = PersonSchema.validate(maya)
    print is_valid
    print errors

    org = {
        'name': 'Startup',
        'ceo': maya,
        'members': [
            adam, john,
            {'name': 'Peter', 'gender': 'M'},
            {'name': 'Martin', 'gender': 'X'}
        ]
    }
    is_valid, errors = OrganizationSchema.validate(org)
    print is_valid
    print errors
