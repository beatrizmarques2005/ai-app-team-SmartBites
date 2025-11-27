
# just a template

"""
Services package - Business logic layer

All domain-specific logic lives here.
Services orchestrate AI calls, tools, and business rules.
"""

# from .contract_service import ContractService

from .ai_service import AIService
from .document_service import DocumentService
from .receipt_service import ReceiptService
from .ingredient_service import IngredientService
from .recipe_crawl_service import RecipeCrawlService
from .recipe_scraper import RecipeScraper

__all__ = ['AIService', 
           'DocumentService',
           'ReceiptService',
           'IngredientService',
           'RecipeCrawlService',
           'RecipeScraper',
           ]
