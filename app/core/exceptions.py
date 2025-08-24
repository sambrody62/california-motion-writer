"""
Custom exceptions
"""

class AppException(Exception):
    """Base application exception"""
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(self.detail)