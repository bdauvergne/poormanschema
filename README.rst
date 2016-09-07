poormanschema
=============

Simple and effective schema checker::

    >>> from poormanschema import *
    >>> check({'first_name': 1}. [{'first_name': str, 'last_name': str}])
    ValueError: {first_name} should be of type "str"

It can also normalize data::

    >>> check(' 2016-03-23T12:23:12 ', OR(STRIP, ISO8601))
    '2016-03-23T12:23:12'

Or convert them on entry::

    >>> repr(check(['1.3'], [DECIMAL]))
    [Decimal('1.3')]

List of predicates
==================

* `check(data, schema, path='')` - check `data` agains `schema`, prefix error messages with `path`
* `OR(*schemas)` - first schema to match is returned
* `ANY` - can be anything
* `AND(*schemas)` - all schemas must match
* `MANDATORY(schema)` - only useful on dict values, indicate the corresponding key is mandatory, all other keys are optional
* `RE(regexp, repl=None, count=0, flag=0)` - value must be a string matching `regexp`
* `ISO8601` - value must be a string like `'2016-09-07T12:12:34'`
* `NORMALIZE(schema, convert)` - apply schema then apply converter to the result
* `STRIP` - remove starting and ending spaces
* `LOWER` - lowercase the string
* `UPPER` - uppercase the string
* `DECIMAL` - convert a string into a decimal.Decimal object

Exemple: SCIM 1.0 Core Schema of an User object
===============================================

::

        schema = {
            'schemas': MANDATORY([basestring]),
            'id': MANDATORY(basestring),
            'externalId': MANDATORY(basestring),
            'userName': MANDATORY(unicode),
            'name': MANDATORY({
                'formatted': MANDATORY(str),
                'familyName': str,
                'givenName': str,
                'middleName': str,
                'honorificPrefix': str,
                'honorificSuffix': str,
            }),
            'urn:ietf:params:scim:schemas:extension:enterprise:2.0:User': MANDATORY({
                'employeeNumber': OR(STRIP, RE(r'^\d+$')),
                'costCenter': OR(STRIP, RE(r'^\d+$')),
            }),
            'meta': {
                'resourceType': 'User',
                'created': ISO8601,
                'lastModified': ISO8601,
                'version': RE(r'^(W\\)?"[^"]"$'),
                'location': str,
            }
        }
