"""Domain modules package.

Importing ``oe_infrastructure.modules`` registers every ORM model on
``Base.metadata`` so that ``init_schema`` and Alembic autogenerate see the
full schema.
"""

import oe_infrastructure.modules.attendance  # noqa: F401,E402
import oe_infrastructure.modules.audit  # noqa: F401,E402

# Module imports register models on Base.metadata.
import oe_infrastructure.modules.auth  # noqa: F401,E402  (User, TokenRevocation)
import oe_infrastructure.modules.credentials  # noqa: F401,E402
import oe_infrastructure.modules.events  # noqa: F401,E402
import oe_infrastructure.modules.identity  # noqa: F401,E402
import oe_infrastructure.modules.organizations  # noqa: F401,E402  (Organization, School)
import oe_infrastructure.modules.sync  # noqa: F401,E402
from oe_infrastructure.modules.base import Base

__all__ = ["Base"]
