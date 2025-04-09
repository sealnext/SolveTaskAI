from datetime import UTC, datetime
from functools import partial

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

utc_now = partial(datetime.now, UTC)


class Base(AsyncAttrs, MappedAsDataclass, DeclarativeBase):
	pass
