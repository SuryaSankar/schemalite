# SchemaLite

A Schema validation library with a very minimal API.

##Installation

	pip install schemalite

##Why another schema library?

Because I started writing it before I came across Cerberus, Marshmallow and Schema.

And also because, while the other libraries have powerful DSLs, they also have too big an API for my simple needs. This library has only one concept I need to keep in mind - A validator is a function that will return a tuple like (False, "Some error message") or (True, None). Thats all.


A schema is a `dict` with 2 keys - "fields" and "validators"

`validators` is a list of validator functions to apply on the input data as a whole instead of at field level. It should again be a function which returns a tuple as output, while accepting a single dictionary as input ( corresponding to the whole input data )

`fields` - is a dict with keys corresponding to the names of the keys of the dictionary which is being validated. Each field is in turn a dict, which has one or more of the following optional keys

1. `required` - True/False. Alternatively it can also be a function which accepts the input dictionary and outputs True/False as output. If not specified, field is assumed to be not required.

2. `type` - The type of the data the field is expecting. It can be any valid pythonic type - int / str / unicode / date / datetime / Decimal / list / dict ( or anything else which is a python `type`). It can also be a list of types in which case the data should be of any one of those types.

3. `validators` - A list of validator functions. The function should accept 2 arguments - The value of the particular key being processed and the whole dictionary itself (in case the validator needs access to the whole data instead of that field alone to decide whether the value is valid). It has to return a tuple. Either (True, None) or (False, "some error message") ( The error need not be a string. It can be any valid json serializable data structure - a list or dict also)

4. `permitted_values` - A list of permitted values for the field.

5. If `type` is list, you can send the following fields also

    i. `list_item_type` - Tells the type of each item in the list. It can also be any Python type or a list of types.
    ii. `list_item_schema` - If `list_item_type` is dict, then you can optionally provide `list_item_schema` also - to validate each dict in the list against another schema

6. If `type` is dict, then you can send the following field
    `dict_schema` - The schema to validate the dict against.


At both field and schema level, all validators will be applied one after another and their errors will be collected together in the output. 

To apply the validator, you can call   `validate_object(schema, data)` ( or `validate_list_of_objects(schema, datalist)`)

The output itself will be tuple of the same format as what we defined above for validators.

Example:

Lets define 2 schemas

```python
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
                lambda person: person['gender']=='Female',
                "Required if gender is female"),
            "type": int,
            "validators": [
                func_and_desc(
                    lambda age, person: (False, "Too old")
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
            lambda org: (False, "Non member cannot be CEO")
            if org["ceo"] not in org["members"] else (True, None),
            "Non member cannot be CEO")
    ],
    "allow_unknown_fields": True
}

```

And some data to validate against the schema

```python
    isaac = {"gender": "Male", "name": "Isaac", "age": "new", "access_levels": [1,4,60]}
    surya = {"gender": "Male", "name": "Surya", "age": "h", "city": "Chennai"}
    senthil = {"gender": "Male", "name": "Senthil"}
    mrx = {"gender": "m", "name": "x"}
    sharanya = {
        "gender": "Female", "name": "Sharanya",
        "access_levels": [4, 5, 60]}
```

Lets first validate some persons

```python
validate_object(person_schema, mrx)
```
Output is

```python
(False,
 {
    'FIELD_LEVEL_ERRORS': {
        'gender': {
            'PERMITTED_VALUES_ERROR': 'Field data can be one of the following only: Male/Female'
        }
    }
})
 ```

Another person

```python
validate_object(person_schema, surya)
```

Output

```python
(False,
 {
    'FIELD_LEVEL_ERRORS': {
        'age': {
            'HAS_TO_BE_LESS_THAN_40': 'Too old',
            'TYPE_ERROR': 'Field data should be of type int'
        }
    },
  'UNKNOWN_FIELDS': ['city']
})
```

Now validating the same person, but allowing unknown fields

```python
validate_object(person_schema, surya)
```

Output

```python
(False,
 {
    'FIELD_LEVEL_ERRORS': {
        'age': {
            'HAS_TO_BE_LESS_THAN_40': 'Too old',
            'TYPE_ERROR': 'Field data should be of type int'
        }
    }
})
```

Finally lets create an organization and validate it

```python
inkmonk = {
    "name": "Inkmonk",
    "ceo": isaac,
    "members": [surya, senthil, sharanya],
    "city": "Chennai"
}
validate_object(org_schema, inkmonk, allow_unknown_fields=False)
```

Output


```python

(False,
{
    'FIELD_LEVEL_ERRORS': {
        'ceo': {
            'VALIDATION_ERRORS_FOR_OBJECT': {
                'FIELD_LEVEL_ERRORS': {
                    'access_levels': {
                        'VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST': [
                            None,
                            None,
                            {
                                'PERMITTED_VALUES_ERROR': 'Field data can be one of the following only: 1/2/3/4/5/6/7/8/9'
                            }
                        ]
                    },
                    'age': {
                        'HAS_TO_BE_LESS_THAN_40': 'Too old',
                        'TYPE_ERROR': 'Field data should be of type int'
                    }
                }
            }
        },
        'members': {
            'VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST': [
                {
                    'FIELD_LEVEL_ERRORS': {
                        'age': {
                            'HAS_TO_BE_LESS_THAN_40': 'Too old',
                            'TYPE_ERROR': 'Field data should be of type int'
                        }
                    },
                    'UNKNOWN_FIELDS': ['city']
                },
                None,
                {
                    'FIELD_LEVEL_ERRORS': {
                        'access_levels': {
                            'VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST': [
                                None,
                                None,
                                {
                                    'PERMITTED_VALUES_ERROR': 'Field data can be one of the following only: 1/2/3/4/5/6/7/8/9'
                                }
                            ]
                        },
                        'age': {
                            'MISSING_FIELD_ERROR': 'Required if gender is female'
                        }
                    },
                    'MISSING_FIELDS': ['age']
                }
            ]
        }
    },
  'SCHEMA_LEVEL_ERRORS': ['Non member cannot be CEO'],
  'UNKNOWN_FIELDS': ['city']
})
```

###Understanding the errors output

The library is structured to provide an error output to any nested level of granularity.

At the outer most level, there are the following keys 

"FIELD_LEVEL_ERRORS" - Contains the errors mapped to each field

"SCHEMA_LEVEL_ERRORS" - A list of errors found for the schema as a whole

"UNKNOWN_FIELDS" - If the validation is configured to not allow unknown fields and if the data had any, they will be listed here

"MISSING_FIELDS" - List of all missing required fields.

Inside 'FIELD_LEVEL_ERRORS', each field will have a dict of errors mapped to it. The keys of the dict are the names of the errors and values are the error strings. Example for an error dict for a field would be 
    `{'TYPE_ERROR': "This field should have type int only"}` or `{"PERMITTED_VALUES_ERROR": "The object should have value high/low only"}

If a particular field is of type `dict`, and if `dict_schema` is defined, then you can also expect to see a key named `VALIDATION_ERRORS_FOR_OBJECT` inside `errors['FIELD_LEVEL_ERRORS']['particular_field_name']`.  In that case `errors['FIELD_LEVEL_ERRORS']['particular_field_name']['VALIDATION_ERRORS_FOR_OBJECT']` will contain another errors object obtained by matching the data in this field alone against another schema ( So that errors object will in turn have FIELD_LEVEL_ERRORS, SCHEMA_LEVEL_ERRORS etc)

If a particular field is of type `list` and if `list_type` is defined, then if there are validation errors for the objects in the list, you can expect to see `errors['FIELD_LEVEL_ERRORS']['particular_field_name']['VALIDATION_ERRORS_FOR_OBJECTS_IN_LIST']`. This will be a list of error objects. If the field is a list of primitive types, then you can expect each error object to have fields like `TYPE_ERROR` or `PERMITTED_VALUES_ERROR`.
If it is a list of objects of another schema ( defined by `list_item_schema`), then each item in the errors list would be an error object got by validating against that schema - so it will have `FIELD_LEVEL_ERRORS`, `SCHEMA_LEVEL_ERRORS` etc. ( While iterating, if one item has no error, then instead of error object, it will have a null in the errors list at that index.)


Since the errors are shown at all levels - it becomes possible to directly apply this on a GUI client for example ( the errors can be shown granularly next to each nested field.)

(Check the full example at example.py)

The decorator `func_and_desc` is used to give a human readable name to a validator. If this is used, when the schema is serialized, the validators will also have readable names. If this decorator is not used, the validator will get serialized using the function name (or `Unnamed function` if there is no function name)

I've also defined some ready to use validators for type checking like shown in the above example. Since the concept of a validator is very generic, it is easy to build a large collection of validators which you can pick and use for your domain.