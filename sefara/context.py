"""
Context is a mapping object that supports substitutions, a "parent" object,
and attribute-based access.

This is heavily inspired by the AttrDict project, and uses some of their
code.

"""
from collections import Mapping, MutableMapping, Sequence
import re
import string
from sys import version_info

# Python 2
PY2, STRING = (True, basestring) if version_info < (3,) else (False, str)

class Context(MutableMapping):
    """
    A mapping object that allows access to its values both as keys, and
    as attributes (as long as the attribute name is a valid identifier).
    """
    def __init__(self, mapping=None, parent=None, substitutions=True):
        if mapping is None:
            mapping = {}
        self.__setattr__('_mapping', mapping, force=True)
        self.__setattr__('_parent', parent, force=True)
        self.__setattr__('_substitutions', substitutions, force=True) 

    def get(self, key, default=None):
        """
        Get a value associated with a key.
        key: The key associated with the desired value.
        default: (optional, None) The value to return if the key is not
            found.
        """
        try:
            return self[key]
        except KeyError:
            return default

    def items(self):
        """
        Returns a list of (key, value) pairs as 2-tuples.
        """
        return [(key, self.get(key)) for key in self.keys()]

    def keys(self):
        """
        Returns a list of keys in the mapping.
        """
        return list(self._mapping)

    def values(self):
        """
        Returns a list of values in the mapping.
        """
        return [value for (key, value) in self.items()]

    def _set(self, key, value):
        """
        Responsible for actually adding/changing a key-value pair. This
        needs to be separated out so that setattr and setitem don't
        clash.
        """
        self._mapping[key] = value

    def _delete(self, key):
        """
        Responsible for actually deleting a key-value pair. This needs
        to be separated out so that delattr and delitem don't clash.
        """
        del self._mapping[key]

    def __getattr__(self, key):
        """
        value = adict.key
        Access a value associated with a key in the instance.
        """
        if key.startswith('_'):
            raise AttributeError(key)
        return self.__getitem__(key)
        
    def __setattr__(self, key, value, force=False):
        """
        adict.key = value
        Add a key-value pair as an attribute
        """
        if force:
            super(Context, self).__setattr__(key, value)
        else:
            if not self._valid_name(key):
                raise TypeError("Invalid key: {0}".format(repr(key)))
            self._set(key, value)

    def __delattr__(self, key):
        """
        del adict.key
        Remove a key-value pair as an attribute.
        """
        if not self._valid_name(key) or key not in self._mapping:
            raise TypeError("Invalid key: {0}".format(repr(key)))
        self._delete(key)

    def __setitem__(self, key, value):
        """
        adict[key] = value
        Add a key-value pair to the instance.
        """
        self._set(key, value)

    def __getitem__(self, key):
        """
        value = adict[key]
        Access a value associated with a key in the instance.
        """
        raw = self._get_item_no_substitutions(key)
        return self._substitute(raw)

    def _substitute(self, obj):
        if not self._substitutions:
            pass
        elif isinstance(obj, Mapping):
            obj = Context(obj, parent=self, substitutions=True)
        elif isinstance(obj, STRING):
            obj = string.Template(obj).safe_substitute(self)
        elif isinstance(obj, Sequence):
            obj = [self._substitute(element) for element in obj]
        return obj

    def _get_item_no_substitutions(self, key):
        try:
            return self._mapping[key]
        except KeyError:
            if self._parent is not None:
                return self._parent._get_item_no_substitutions(key)
        raise KeyError(key)

    def __delitem__(self, key):
        """
        del adict[key]
        Delete a key-value pair in the instance.
        """
        self._delete(key)

    def __contains__(self, key):
        """
        key in adict
        Check if a key is in the instance.
        """
        if key in self._mapping:
            return True
        if self._parent is not None:
            return key in self._parent
        return False

    def __len__(self):
        """
        len(adict)
        Check the length of the instance.
        """
        return len(self.keys())

    def __iter__(self):
        """
        (key for key in adict)
        iterate through all the keys.
        """
        return iter(self.keys())

    def __repr__(self):
        """
        Create a string representation of the Context.
        """
        return ("<Context: %s>" %
            " ".join("%s=%s" % (key, value) for (key, value) in self.items()))  

    def __getstate__(self):
        """
        Handle proper serialization of the object. (used by pickle).
        """
        return (self._mapping, self._parent, self._substitutions) 

    def __setstate__(self, state):
        """
        Handle proper deserialization of the object. (used by pickle).
        """
        (mapping, parent, substitutions) = state
        self.__init__(mapping, parent, substitutions)

    # For ipython auto complete
    def __dir__(self):
        result = list(self.__dict__.keys())
        result.extend(self.keys())
        return result

    @property
    def raw(self):
        return Context(
            self._mapping,
            self._parent,
            substitutions=False)

    @classmethod
    def _valid_name(cls, name):
        """
        Check whether a key name is a valid attribute name. A valid
        name must start with an alphabetic character, and must only
        contain alphanumeric characters and underscores. The name also
        must not be an attribute of this class.
        NOTE: Names with leading underscores are considered invalid for
        stylistic reasons. While this package is fairly un-Pythonic, I'm
        going to stand strong on the fact that leading underscores
        represent private attributes. Further, magic methods absolutely
        need to be prevented so that crazy things don't happen.
        """
        return (isinstance(name, STRING) and
                re.match('^[A-Za-z][A-Za-z0-9_]*$', name) and
                not hasattr(cls, name))

