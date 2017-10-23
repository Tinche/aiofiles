from .utils import (delegate_to_executor, proxy_property_directly,
                    proxy_method_directly)
from ..base import AsyncBase


@delegate_to_executor('close', 'flush', 'isatty', 'read', 'readable',
                      'readline', 'readlines', 'seek', 'seekable', 'tell',
                      'truncate', 'write', 'writable', 'writelines')
@proxy_method_directly('detach', 'fileno', 'readable')
@proxy_property_directly('buffer', 'closed', 'encoding', 'errors',
                         'line_buffering', 'newlines')
class AsyncTextIOWrapper(AsyncBase):
    """The asyncio executor version of io.TextIOWrapper."""
