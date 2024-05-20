__version__ = "5.0a0"

# Check Django compatibility before other imports which may fail if the
# wrong version of Django is installed.
from .utils import check_django_compatability

check_django_compatability()

from .expressions import register_expressions  # noqa: E402
from .functions import register_functions  # noqa: E402
from .lookups import register_lookups  # noqa: E402
from .query import register_nodes  # noqa: E402

register_expressions()
register_functions()
register_lookups()
register_nodes()
