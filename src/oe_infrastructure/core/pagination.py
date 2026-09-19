"""Pagination helpers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    has_more: bool

    @classmethod
    def build(
        cls,
        items: Sequence[T],
        total: int,
        page: int,
        size: int,
    ) -> Page[T]:
        return cls(
            items=list(items),
            total=total,
            page=page,
            size=size,
            has_more=(page * size) < total,
        )


def offsets(page: int, size: int) -> tuple[int, int]:
    return (page - 1) * size, size
