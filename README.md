# SchemaLite

A Schema validation library with a very minimal API.

##Installation

	pip install schemalite

##Why another schema library?

Because I started writing it before I came across Cerberus, Marshmallow and Schema.

And also because, while the other libraries have powerful DSLs, they also have too big an API for my simple needs. This library has only one concept I need to keep in mind - A validator is a function that will return a tuple like (False, "Some error message") or (True, None). Thats all.

Example for a schema object:

```python
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
    }
}

org_schema = {
    "fields": {
        "name": {
            "required": True
        },
        "ceo": {
            "target_schema": person_schema,
            "targe_relation_type": "scalar"
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
    ]
}
```

A schema is a `dict` with 2 keys - "fields" and "validators"

`fields` - is a dict with keys corresponding to the names of the keys of the dictionary which is being validated. Each field is in turn a dict, which has one or more of the following optional keys

    `required` - True/False. Alternatively it can also be a function which accepts the input dictionary and outputs True/False as output. 

    `validators` - A list of validator functions. The function should accept 2 arguments - The value of the particular key being processed and the whole dictionary itself (in case the validator needs access to the whole data instead of that field alone to decide whether the value is valid).
    It has to return a tuple. Either (True, None) or (False, "some error message") ( The error need not be a string. It can be any valid json serializable data structure - a list or dict also)

    `schema` - You can nest schemas. If a particular key should be used to store an object or list of objects which correspond to another schema, refer that another schema here.

    `rel_type` - This will be checked only when `schema` attribute is set. This defines how that schema is related. It can take 2 values currently - `scalar` ( if it maps to a single object on the target side , Eg: order.user ) or `list` (if it maps to a list of objects, eg: user.orders )

`validators` is a list of validator functions to apply on the input data as a whole instead of at field level. It should again be a function which returns a tuple as output, while accepting a single dictionary as input ( corresponding to the whole input data )

At both field and schema level, all validators will be applied one after another and their errors will be collected together in the output. 

To apply the validator, you can call   `validate_object(schema, data)` ( or `validate_list_of_objects(schema, datalist)`)

The output itself will be tuple of the same format as what we defined above for validators.

Sample output

```python
(
    False,
    {
        'FIELD_LEVEL_ERRORS': {
            'members': [
                [{
                    'FIELD_LEVEL_ERRORS': {'age': ['TypeError', 'Too old']}
                  },
                  None,
                  {
                    'MISSING_FIELDS': ['age']
                   }
                ]
            ]
        },
        'SCHEMA_LEVEL_ERRORS': ['Non member cannot be CEO']
    }
)
```

Here the input data had a list of objects called members. The first memeber had some field level errors. The third member had some schema level errors. The second member had no errors.

Since the errors are shown at all levels - it becomes very easy to directly apply this on a GUI client for example ( the errors can be shown granularly next to each nested field.)

Here is a full example

```python
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
    }
}

org_schema = {
    "fields": {
        "name": {
            "required": True
        },
        "ceo": {
            "schema": person_schema,
            "rel_type": "scalar"
        },
        "members": {
            "schema": person_schema,
            "rel_type": "list"
        }
    },
    "validators": [
        func_and_desc(
            lambda org: (False, "Non member cannot be CEO")
            if org["ceo"] not in org["members"] else (True, None),
            "Non member cannot be CEO")
    ]
}


if __name__ == '__main__':
    isaac = {"gender": "Male", "name": "Isaac"}
    surya = {"gender": "Male", "name": "Surya", "age": "h"}
    senthil = {"gender": "Male", "name": "Senthil"}
    sharanya = {"gender": "Female", "name": "Sharanya"}
    inkmonk = {
        "name": "Inkmonk",
        "ceo": isaac,
        "members": [surya, senthil, sharanya]

    }
    print validate_object(person_schema, surya)
    print validate_object(org_schema, inkmonk)

    print json.loads(schema_to_json(person_schema))

    print json.loads(schema_to_json(org_schema))
```

The decorator `func_and_desc` is used to give a human readable name to a validator. If this is used, when the schema is serialized, the validators will also have readable names. If this decorator is not used, the validator will get serialized using the function name (or `Unnamed function` if there is no function name)

I've also defined some ready to use validators for type checking like shown in the above example. Since the concept of a validator is very generic, it is easy to build a large collection of validators which you can pick and use for your domain.