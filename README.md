# SchemaLite

A Schema validation library with a very minimal API.

##Installation

	pip install schemalite

##Why another schema library?

Because I started writing it before I came across cerberus and schema.

And also because, while Cerberus and Schema are very powerful, they also have too big an API for my simple needs. This library has only  two concepts I need to keep in mind. 


    1. Define a Schema class with Fields, just like one will write a WTForm class with Fields or a SQLalchemy Model with Columns

    2. Each field can have a validator. A validator is defined as a function which accepts a value as input and returns a tuple as output. The first element of the tuple is a boolean - denoting whether the value is valid or not. The second element represents the error, in case the value is invalid. The error can be represented any way you like - a String, or a dictionary or a list of strings or a list of dictionaries - anything. Your app, your validator, your rules.

Using composition, we can map complex data types with just the single concept of validator.


##Example Usage


```python

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


```
