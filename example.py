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
            "required": True,
            "type": (str, unicode)
        },
        "gender": {
            "required": True,
            "type": (str, unicode),
            "permitted_values": ("Male", "Female")
        },
        "age": {
            "required": func_and_desc(
                lambda person, schema, context: person.get('gender')=='Female',
                "Required if gender is female"),
            "type": int,
            "validators": [
                func_and_desc(
                    lambda age, person, schema, context: (False, "Too old")
                    if age > 40 else (True, None),
                    "Has to be less than 40")
            ]
        },
        "access_levels": {
            "type": list,
            "list_item_type": int,
            "permitted_values_for_list_items": range(1, 10)
        }
    },
}

org_schema = {
    "fields": {
        "name": {
            "required": True,
            "type": (str, unicode)

        },
        "ceo": {
            "required": True,
            "type": dict,
            "dict_schema": person_schema
        },
        "members": {
            "required": True,
            "type": list,
            "list_item_type": dict,
            "list_item_schema": person_schema
        }
    },
    "validators": [
        func_and_desc(
            lambda org, schema, context: (False, "Non member cannot be CEO")
            if org.get("ceo") not in org.get("members") else (True, None),
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
    isaac = {"gender": "Male", "name": "Isaac", "age": "new", "access_levels": [1,4,60]}
    surya = {"gender": "Male", "name": "Surya", "age": "h", "city": "Chennai"}
    senthil = {"gender": "Male", "name": "Senthil"}
    mrx = {"gender": "m", "name": "x"}
    sharanya = {
        "gender": "Female", "name": "Sharanya",
        "access_levels": [4, 5, 60]}
    inkmonk = {
        "name": "Inkmonk",
        "ceo": isaac,
        "members": [surya, senthil, sharanya],
        "city": "Chennai"
    }
    print validate_object(person_schema, sharanya)
    print validate_object(person_schema, mrx)
    print validate_object(person_schema, surya)
    print validate_object(person_schema, surya, allow_unknown_fields=True)
    print validate_object(org_schema, inkmonk)
    print validate_object(org_schema, inkmonk, allow_unknown_fields=False)
    print validate_object(person_schema, {}, allow_required_fields_to_be_skipped=True)
    print validate_object(person_schema, {})

    # print json.loads(schema_to_json(person_schema))

    # print json.loads(schema_to_json(org_schema))

    # ds = {
    #     "attrs": ["id"],
    #     "rels": {
    #         "user": {
    #             "attrs": ["id"]
    #         }
    #     }
    # }

    # print validate_object(ds_schema, ds)

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
