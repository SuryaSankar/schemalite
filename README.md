# SchemaLite

A Schema validation library with a very minimal API and an interface that looks very similar to form validation libraries and ORMs.

##Usage

First define your schemas somewhere

```python

	from schemalite import SchemaLite, Field, SchemaLiteField, SchemaLiteListField


	class PersonSchema(SchemaLite):

	    name = Field(validator=lambda val:
	                 (False, 'NULLVALUE') if val is None else (True, None))
	    gender = Field(validator=lambda val:
	                   (True, None) if val in ['M', 'F']
	                   else (False, 'INVALID_VALUE'))


	class OrganizationSchema(SchemaLite):

	    name = Field(validator=lambda val:
	                 (False, 'NULLVALUE') if val is None else (True, None))
	    head = SchemaLiteField(PersonSchema, required=False)
	    members = SchemaLiteListField(PersonSchema)

```

Then use them in your validation code

```python

    person = {'name': 'Al Capone', 'gender': 'M'}

    validated_person = PersonSchema(person)
    print validated_person.valid
    print validated_person.errors

    org = {
        'name': 'La Cosa Nostra',
        'head': person,
        'members': [
            {'name': 'Ricky', 'gender': 'F'},
            {'name': 'Helen', 'gender': 'F'},
            {'name': 'Helen', 'gender': 'X'}
        ]
    }
    validated_org = OrganizationSchema(org)
    print validated_org.valid
    print validated_org.errors

```
