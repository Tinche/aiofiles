try:
    from functools import singledispatch
except ImportError:                            # pragma: nocover
    from singledispatch import singledispatch
