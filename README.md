# JSchema

A simple pattern for validating JSON objects. Any valid dictionary with string keys is a 
JSON object.

##Usage

First define your schemas somewhere

	def not_none_not_empty(val):
		return val is not None and val.strip() != ''

	
	address_schema = JSchema(
	    {
	    	'key': 'name',
	     	'validator': not_none_not_empty
	    },
	    {
	    	'key': 'contact_number',
	     	'validator': lambda x: not_none_not_empty(x) and x.isdigit(),
	     	'error_message': lambda x: 'Null value' if not_none_not_empty(x) else 'Invalid Value'
	    },
	    {
	    	'key': 'company_name', 'required': False
	    },
	    {
	    	'key': 'address_line_1',
	     	'validator': not_none_not_empty
	    },
	    {
	    	'key': 'address_line_2', 'required': False
	    },
	    {
	    	'key': 'landmark', 'required': False
	    },
	    {
	    	'key': 'city', 'validator': not_none_not_empty
	    },
	    {
	    	'key': 'state', 'validator': not_none_not_empty
	    },
	    'country',
	    {
	    	'key': 'postal_code', 'validator': not_none_not_empty
	    })


Then in your application code


	address_data = request.json.get('shipping_address') # Or some other input data

	if address_schema.validates(address_data):
		# do something with address_data
		print address_data
	else:
		# You can get the errors as a neat dictionary when it fails
		print address_schema.validation_errors(address_data)
