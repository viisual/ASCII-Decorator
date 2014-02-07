import imp
import os
import re
import inspect

try:
    from StringIO import StringIO
except:
    from io import BytesIO as StringIO


# In Sublime Text 2, the CWD is always changing,
# So when we try and guess the modules path,
# it gives us relative paths to...I have no idea where.
# To fix the relative path issue, we require ST2 to give
# the path everything will be relative to.  And we ensure
# that we change to that directory when evaluating the modules.
REL_PATH = None


def set_relative_path(pth):
    global REL_PATH
    REL_PATH = pth


def _get_path(module):
    attr = None
    if REL_PATH is not None:
        os.chdir(REL_PATH)
    try:
        m = __import__(module)
    except:
        m = None

    if m is not None:
        parts = module.split('.')
        parts.pop(0)
        attr = m
        while len(parts):
            attr = getattr(attr, parts.pop(0))

    if attr is not None:
        if REL_PATH is not None:
            attr = os.path.normpath(os.path.join(REL_PATH, attr.__path__[0]))
        else:
            attr = os.path.normpath(attr.__path__[0])

    return attr if attr is not None else None


def resource_exists(module, resource):
    found = False
    found_path = _get_path(module)
    if found_path is not None:
        found = os.path.exists(os.path.join(found_path, resource))
    return found


def resource_string(module, resource):
    data = None
    found_path = _get_path(module)
    if found_path is not None:
        file_path = os.path.join(found_path, resource)
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                data = f.read()
    return data


def resource_listdir(module, resource):
    found_path = _get_path(module)
    if found_path is not None:
        file_path = os.path.join(found_path, resource)
        if os.path.exists(file_path):
            return os.listdir(file_path)
    return None


def resource_stream(module, resource):
    data = resource_string(module, resource)
    return StringIO(data) if data is not None else data
