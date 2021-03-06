import re
import decimal


def OR(*args):
    def f(data, path):
        errors = []
        for schema in args:
            try:
                new_data = check(data, schema, path)
            except ValueError, e:
                errors.append(e)
            else:
                return new_data
        else:
            if errors:
                raise ValueError(' or '.join([error.args[0] for error in errors]))
            return data
    return f

ANY = OR()


def AND(*args):
    def f(data, path):
        errors = []
        for schema in args:
            try:
                data = check(data, schema, path)
            except ValueError, e:
                errors.append(e)
        if errors:
            raise ValueError(' and '.join([error.args[0] for error in errors]))
        return data
    return f


def MANDATORY(schema):
    def f(data, path):
        return check(data, schema, path)
    f.mandatory = True
    return f


def RE(regexp, repl=None, count=0, flags=0, msg=None):
    pattern = regexp if hasattr(regexp, 'match') else re.compile(regexp, flags=flags)

    def f(data, path):
        assert isinstance(data, basestring), '%s should be a basestring' % path
        assert pattern.match(data), '%s(=="%s") %s' % (
            path, data[:100], msg or 'does not match /%s/' % regexp)
        if repl:
            return pattern.sub(repl, data, count=count)
        else:
            return data
    return f

ISO8601_DATETIME = RE(r'^\d+-\d+-\d+T\d+:\d+:\d+(?:\.\d+)?(?:Z|\d+:\d+)?$')

ISO8601_DATE = RE(r'^\d+-\d+-\d+$')

ISO8601_TIME = RE(r'\d+:\d+:\d+(?:\.\d+)?$')

BASE64 = RE('^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$', msg='is not base64')


def NORMALIZE(schema, converter):
    def f(data, path):
        data = check(data, schema, path)
        return converter(data)
    return f


def __parse_datetime(data):
    import isodate
    return isodate.parse_datetime(data)


def __parse_date(data):
    import isodate
    return isodate.parse_date(data)


def __parse_time(data):
    import isodate
    return isodate.parse_time(data)

DATETIME = NORMALIZE(ISO8601_DATETIME, __parse_datetime)

DATE = NORMALIZE(ISO8601_DATE, __parse_date)

TIME = NORMALIZE(ISO8601_TIME, __parse_time)

STRIP = NORMALIZE(basestring, lambda s: s.strip())

LOWER = NORMALIZE(basestring, lambda s: s.lower())

UPPER = NORMALIZE(basestring, lambda s: s.upper())

DECIMAL = NORMALIZE(basestring, decimal.Decimal)


def check(data, schema, path=''):
    try:
        return check1(data, schema, path)
    except AssertionError, e:
        raise ValueError(*e.args)


def check1(data, schema, path=''):
    if not isinstance(schema, type) and callable(schema):
        return schema(data, path)
    t = schema if isinstance(schema, type) else type(schema)
    if t is list:
        assert isinstance(data, list), '%s should be a list' % path
        if len(schema):
            assert len(schema) == 1, 'schema lists must have at most one element'
            l = []
            for i, e in enumerate(data):
                l.append(check(e, schema[0], path + '[%s]' % i))
            return l
        return data
    elif t is dict:
        assert isinstance(data, dict), '%s should be a dict' % path
        if len(schema):
            mandatory_keys = [key for key in schema if hasattr(schema.get(key), 'mandatory')]
            errors = []
            if not (set(data.keys()) <= set(schema.keys())):
                errors.append('%s keys(%s) are not a subset of %s'
                              % (path, ', '.join(sorted(data.keys())),
                                 ', '.join(sorted(schema.keys))))
            if not (set(mandatory_keys) <= set(data.keys())):
                errors.append('%s keys(==%s) are not a superset of %s'
                              % (path, ', '.join(sorted(data.keys())),
                                 ', '.join(sorted(mandatory_keys))))
            d = {}
            for key in data:
                if key in schema:
                    try:
                        d[key] = check(data[key], schema[key], path + '{%s}' % key)
                    except ValueError, e:
                        errors.append(e.args[0])
            if errors:
                raise ValueError(' and '.join(error for error in errors))
            return d
        return data
    elif isinstance(schema, basestring):
        assert data == schema, '%s value should be %s, but it\'s %s' % (path, schema, data)
        return data
    else:
        assert isinstance(data, t), '%s should be of type "%s"' % (path, t.__name__)
        return data

if __name__ == '__main__':
    schema = [
        {
            'a': MANDATORY(OR(None, int, OR(STRIP, ISO8601_DATETIME))),
            'b': str,
            'c': RE('^a*$'),
            'd': ISO8601_DATE,
            'e': ISO8601_TIME,
            'f': BASE64,
        }
    ]

    def tryit(a, b, fail=True):
        try:
            return check(a, b)
        except ValueError, e:
            print e
            if not fail:
                raise
        else:
            if fail:
                raise Exception('it dit not fail %s %s' % (a, b))

    tryit(1, schema)
    tryit([], schema, fail=False)
    tryit([{'f': 'x'}], schema)
    tryit([{'a': 1}], schema, fail=False)
    tryit([{'a': 1, 'd': '1023-02-02', 'e': '12:12:12'}], schema, fail=False)
    tryit([{'a': None}], schema, fail=False)
    print tryit([{'a': ' 2016-12-01T09:34:34 '}], schema, fail=False)
    tryit([{'a': 1, 'b': 2, 'c': 'b'}], schema)
    tryit([{'b': 'x'}], schema)
    print repr(tryit('1.3', DECIMAL))
