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


if __name__ == '__main__':
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
