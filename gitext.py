import re


def source_read_callback(app, docname, source):
    content = source[0]
    content = re.sub(r'#(\d+)', r':issue:`\1`', content)
    content = re.sub(r'([\d[a-fA-F]{7,})', r':sha:`\1`', content)
    source[0] = content


def setup(app):
    app.connect('source-read', source_read_callback)

    return {'version': '0.1'}
