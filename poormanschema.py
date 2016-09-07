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


def RE(regexp, repl=None, count=0, flags=0):
    pattern = regexp if hasattr(regexp, 'match') else re.compile(regexp, flags=flags)

    def f(data, path):
        assert isinstance(data, basestring), '%s should be a basestring' % path
        assert pattern.match(data), '%s(=="%s") does not match /%s/' % (
            path, data[:100], regexp)
        if repl:
            return pattern.sub(repl, data, count=count)
        else:
            return data
    return f

ISO8601 = RE(r'\d+-\d+-\d+T\d+:\d+:\d+(\.\d+)?(Z|\d+:\d+)?$')


def NORMALIZE(schema, converter):
    def f(data, path):
        data = check(data, schema, path)
        return converter(data)
    return f

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
            assert set(data.keys()) <= set(schema.keys()), (
                '%s keys(%s) are not a subset of %s' % (path, ', '.join(sorted(data.keys())),
                                                        ', '.join(sorted(schema.keys))))
            assert set(mandatory_keys) <= set(data.keys()), (
                '%s keys(==%s) are not a superset of %s' % (path, ', '.join(sorted(data.keys())),
                                                            ', '.join(sorted(mandatory_keys))))
            errors = []
            d = {}
            for key in data:
                try:
                    d[key] = check(data[key], schema[key], path + '{%s}' % key)
                except ValueError, e:
                    errors.append(e)
            if errors:
                raise ValueError(' and '.join(error.args[0] for error in errors))
            return d
        return data
    elif isinstance(schema, basestring):
        assert data == schema, '%s value should be %s, but it\'s %s' % (path, schema, data)
        return data
    else:
        assert isinstance(data, t), '%s should be of type "%s"' % (path, t.__name__)
        return data

schema = [{'a': MANDATORY(OR(None, int, OR(STRIP, ISO8601))), 'b': str, 'c': RE('^a*$')}]


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


if __name__ == '__main__':
    tryit(1, schema)
    tryit([], schema, fail=False)
    tryit([{'a': 1}], schema, fail=False)
    tryit([{'a': None}], schema, fail=False)
    print tryit([{'a': ' 2016-12-01T09:34:34 '}], schema, fail=False)
    tryit([{'a': 1, 'b': 2, 'c': 'b'}], schema)
    tryit([{'b': 'x'}], schema)
    print repr(tryit('1.3', DECIMAL))
