
# just a template

"""
Services package - Business logic layer

All domain-specific logic lives here.
Services orchestrate AI calls, tools, and business rules.
"""

# from .contract_service import ContractService

from .ai_service import AIService
from .auth_service import AuthService

__all__ = [
    'AIService',
    'AuthService',
]
