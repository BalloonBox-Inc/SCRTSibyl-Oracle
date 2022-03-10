import time

def timeit(method):
    def timed(*args, **kw):
        t0 = time.time()
        result = method(*args, **kw)
        t1 = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((t1 - t0) * 1000)
        else:
            # time length
            span = (t1 - t0) * 1000 # milliseconds
            if span >= 1000:
                span = span / 1000 # seconds
                if span >= 60:
                    span = str(round(span / 60, 2)) + ' min' # minutes
                else:
                    span = str(round(span, 2)) + ' sec' # seconds
            else:
                span = str(round(span, 2)) + ' ms' # milliseconds
            # function name
            func = method.__name__
            size = len(func)
            if size <= 10:
                print('> %r:\t\t\t\t%s' % (func, span))
            elif size <= 18:
                print('> %r:\t\t\t%s' % (func, span))
            elif size <= 26:
                print('> %r:\t\t%s' % (func, span))
            elif size <= 34:
                print('> %r:\t%s' % (func, span))
            else:
                print('> %r: %s' % (func, span))
        return result
    return timed
