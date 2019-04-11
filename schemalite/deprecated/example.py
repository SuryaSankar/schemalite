from schemalite import Schema, Field, validator, schema_validator, SchemaError, SchemaObjectField, ListOfSchemaObjectsField
from schemalite.validators import type_validator
import json


class PersonSchema(Schema):

    name = Field(required=True)
    gender = Field(required=True)
    age = Field(validator=type_validator(int),
                required=False, internal_name='big_age')

    @classmethod
    @validator('age')
    def validate_age(cls, val, data):
        if val < 0 or val > 120:
            raise SchemaError('Invalid Value For Age')

    @classmethod
    @schema_validator
    def check_males_age(cls, data):
        if data['gender'] == 'M':
            if 'age' in data and data['age'] > 70:
                raise SchemaError('Male age cannot be greater than 70')


class OrganizationSchema(Schema):

    name = Field(required=True)
    head = SchemaObjectField(required=False, schema=PersonSchema)
    members = ListOfSchemaObjectsField(schema=PersonSchema)


if __name__ == '__main__':

    print json.loads(schema_to_json(person_schema))

    print json.loads(schema_to_json(org_schema))

    ds = {
        "attrs": ["id"],
        "rels": {
            "user": {
                "attrs": ["id"]
            }
        }
    }

    print validate_dict(ds_schema, ds)

    ricky = {'gender': 'M', 'age': 80}

    try:
        PersonSchema.validate(ricky)
    except SchemaError as e:
        print e.value
    else:
        print "No error"

    adam = {'name': 'Adam', 'gender': 'M', 'age': -1.4}

    try:
        PersonSchema.validate(adam)
    except SchemaError as e:
        print e.value
    else:
        print "No error"

    john = {'name': 'John', 'gender': 'M', 'age': 200}

    try:
        PersonSchema.validate(john)
    except SchemaError as e:
        print e.value
    else:
        print "No error"

    maya = {'name': 'Maya', 'gender': 'M', 'age': 20}

    try:
        PersonSchema.validate(maya)
    except SchemaError as e:
        print e.value
    else:
        print "No error"

    org = {
        'name': 'Startup',
        'head': maya,
        'members': [
            adam, john,
            {'name': 'Peter', 'gender': 'M'},
            {'name': 'Martin', 'gender': 'X'}
        ]
    }
    try:
        OrganizationSchema.validate(org)
    except SchemaError as e:
        print e.value
    else:
        print "No error"

    ricky = {'name': 'Ricky', 'gender': 'M', 'age': 80}

    try:
        PersonSchema.validate(ricky)
    except SchemaError as e:
        print e.value
    else:
        print "No error"

    print "adapted values"

    print OrganizationSchema.adapt(org)
