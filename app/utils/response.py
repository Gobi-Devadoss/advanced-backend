import math
from typing import Any, List


def success_response(data: Any = None, message: str = "Success") -> dict:
    return {"success": True, "message": message, "data": data}


def error_response(message: str, data: Any = None) -> dict:
    return {"success": False, "message": message, "data": data}


def paginate(items: List[Any], total: int, page: int, page_size: int) -> dict:
    total_pages = math.ceil(total / page_size) if page_size > 0 else 1
    return {
        "success": True,
        "message": "OK",
        "data": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
