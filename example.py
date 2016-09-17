from schemalite import Schema, Field, validator, schema_validator, SchemaError, SchemaObjectField, ListOfSchemaObjectsField
from schemalite.validators import type_validator, is_a_type_of, is_a_list_of_types_of
from schemalite.core import validate_object, schema_to_json, func_and_desc
import json


class PersonSchema(Schema):

    name = Field(required=True)
    gender = Field(required=True)
    age = Field(validator=type_validator(int), required=False, internal_name='big_age')

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


person_schema = {
    "fields": {
        "name": {
            "required": True
        },
        "gender": {
            "required": True,
            "validators": [
                is_a_type_of(str, unicode),
                func_and_desc(
                    lambda gender, person: (False, "Invalid value")
                    if gender not in ("Male", "Female") else (True, None),
                    "Must be either male or female")
            ]
        },
        "age": {
            "validators": [
                is_a_type_of(int),
                func_and_desc(
                    lambda age, person: (False, "Too old")
                    if age > 40 else (True, None),
                    "Has to be less than 40")
            ],
            "required": func_and_desc(
                lambda person: person['gender']=='Female',
                "If gender is female")
        }
    },
}

org_schema = {
    "fields": {
        "name": {
            "required": True
        },
        "ceo": {
            "target_schema": person_schema,
            "target_relation_type": "scalar"
        },
        "members": {
            "target_schema": person_schema,
            "target_relation_type": "list"
        }
    },
    "validators": [
        func_and_desc(
            lambda org: (False, "Non member cannot be CEO")
            if org["ceo"] not in org["members"] else (True, None),
            "Non member cannot be CEO")
    ],
    "allow_unknown_fields": True
}

ds_schema = {
    "fields": {
        "attrs": {
            "required": False,
            "validators": [is_a_list_of_types_of(str, unicode)]
        },
        "rels": {
            "required": False,
            "validators": [is_a_type_of(dict)]
        }
    }
}

def validate_rels(obj):
    for k, v in obj["rels"]:
        validate_object(ds_schema, v)

if __name__ == '__main__':
    isaac = {"gender": "Male", "name": "Isaac"}
    surya = {"gender": "Male", "name": "Surya", "age": "h", "city":"Chennai"}
    senthil = {"gender": "Male", "name": "Senthil"}
    sharanya = {"gender": "Female", "name": "Sharanya"}
    inkmonk = {
        "name": "Inkmonk",
        "ceo": isaac,
        "members": [surya, senthil, sharanya],
        "city": "Chennai"
    }
    print validate_object(person_schema, surya)
    print validate_object(person_schema, surya, True)
    print validate_object(org_schema, inkmonk)
    print validate_object(org_schema, inkmonk, False)

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

    print validate_object(ds_schema, ds)

    # ricky = {'gender': 'M', 'age': 80}

    # try:
    #     PersonSchema.validate(ricky)
    # except SchemaError as e:
    #     print e.value
    # else:
    #     print "No error"

    # adam = {'name': 'Adam', 'gender': 'M', 'age': -1.4}

    # try:
    #     PersonSchema.validate(adam)
    # except SchemaError as e:
    #     print e.value
    # else:
    #     print "No error"

    # john = {'name': 'John', 'gender': 'M', 'age': 200}

    # try:
    #     PersonSchema.validate(john)
    # except SchemaError as e:
    #     print e.value
    # else:
    #     print "No error"

    # maya = {'name': 'Maya', 'gender': 'M', 'age': 20}

    # try:
    #     PersonSchema.validate(maya)
    # except SchemaError as e:
    #     print e.value
    # else:
    #     print "No error"

    # org = {
    #     'name': 'Startup',
    #     'head': maya,
    #     'members': [
    #         adam, john,
    #         {'name': 'Peter', 'gender': 'M'},
    #         {'name': 'Martin', 'gender': 'X'}
    #     ]
    # }
    # try:
    #     OrganizationSchema.validate(org)
    # except SchemaError as e:
    #     print e.value
    # else:
    #     print "No error"

    # ricky = {'name': 'Ricky', 'gender': 'M', 'age': 80}

    # try:
    #     PersonSchema.validate(ricky)
    # except SchemaError as e:
    #     print e.value
    # else:
    #     print "No error"

    # print "adapted values"

    # print OrganizationSchema.adapt(org)
