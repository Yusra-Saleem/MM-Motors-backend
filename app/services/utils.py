from math import ceil

from sqlalchemy.orm import Query

from app.core.pagination import PaginationMeta


def paginate_query(query: Query, page: int, page_size: int):
    total = query.order_by(None).count()
    total_pages = max(1, ceil(total / page_size)) if total else 1
    items = query.limit(page_size).offset((page - 1) * page_size).all()
    return items, PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages)

