import jinja2
from numerize import numerize


def humansize(nbytes, decimals):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    while nbytes >= 1000 and i < len(suffixes)-1:
        nbytes /= 1000.
        i += 1
    f = ('%.{}f'.format(decimals) % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])


