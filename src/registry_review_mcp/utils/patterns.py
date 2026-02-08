"""Pre-compiled regex patterns for document classification and validation."""

import re

# ============================================================================
# Project ID Patterns
# ============================================================================

PROJECT_ID_PATTERN = re.compile(r"C\d{2}-\d+")
PROJECT_ID_STRICT = re.compile(r"^C\d{2}-\d+$")

# ============================================================================
# Date Patterns
# ============================================================================

# ISO format: 2022-08-15
DATE_ISO = re.compile(r"\d{4}-\d{2}-\d{2}")

# Common formats: 08/15/2022, 15/08/2022, Aug 15 2022
DATE_SLASH = re.compile(r"\d{1,2}/\d{1,2}/\d{4}")
DATE_WRITTEN = re.compile(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}", re.IGNORECASE)

# ============================================================================
# Document Classification Patterns (Filename-based)
# ============================================================================

# Project Plan indicators
PROJECT_PLAN_PATTERNS = [
    re.compile(r"project[\s_-]?plan", re.IGNORECASE),
    re.compile(r"pp[\s_-]\d+", re.IGNORECASE),
]

# Baseline Report indicators
BASELINE_PATTERNS = [
    re.compile(r"baseline[\s_-]?report", re.IGNORECASE),
    re.compile(r"baseline[\s_-]?\d+", re.IGNORECASE),
]

# Monitoring Report indicators
MONITORING_PATTERNS = [
    re.compile(r"monitoring[\s_-]?report", re.IGNORECASE),
    re.compile(r"annual[\s_-]?report", re.IGNORECASE),
]

# GHG Emissions indicators
GHG_PATTERNS = [
    re.compile(r"ghg[\s_-]?emissions?", re.IGNORECASE),
    re.compile(r"greenhouse[\s_-]?gas", re.IGNORECASE),
    re.compile(r"carbon[\s_-]?emissions?", re.IGNORECASE),
]

# Land Tenure indicators
LAND_TENURE_PATTERNS = [
    re.compile(r"land[\s_-]?tenure", re.IGNORECASE),
    re.compile(r"lease[\s_-]?agreement", re.IGNORECASE),
    re.compile(r"deed", re.IGNORECASE),
    re.compile(r"title", re.IGNORECASE),
    re.compile(r"official[\s_-]?copy[\s_-]?\(register\)", re.IGNORECASE),
    re.compile(r"land[\s_-]?registry", re.IGNORECASE),
    re.compile(r"\bLT\d{5,}", re.IGNORECASE),
]

# Land Cover / Geographic Boundary indicators
LAND_COVER_PATTERNS = [
    re.compile(r"land[\s_-]?cover[\s_-]?map", re.IGNORECASE),
    re.compile(r"land[\s_-]?cover", re.IGNORECASE),
    re.compile(r"boundary[\s_-]?map", re.IGNORECASE),
    re.compile(r"geographic[\s_-]?boundar", re.IGNORECASE),
]

# Registry Review indicators
REGISTRY_REVIEW_PATTERNS = [
    re.compile(r"registry[\s_-]?agent[\s_-]?review", re.IGNORECASE),
    re.compile(r"credit[\s_-]?issuance[\s_-]?review", re.IGNORECASE),
    re.compile(r"registration[\s_-]?review", re.IGNORECASE),
]

# Methodology Reference indicators
METHODOLOGY_PATTERNS = [
    re.compile(r"methodology", re.IGNORECASE),
    re.compile(r"protocol", re.IGNORECASE),
    re.compile(r"credit[\s_-]?class", re.IGNORECASE),
]

# ============================================================================
# File Type Patterns
# ============================================================================

GIS_EXTENSIONS = {".shp", ".shx", ".dbf", ".prj", ".geojson", ".kml", ".kmz"}
IMAGE_EXTENSIONS = {".tif", ".tiff", ".jpg", ".jpeg", ".png", ".gif"}
PDF_EXTENSION = {".pdf"}
SPREADSHEET_EXTENSIONS = {".xlsx", ".xls", ".csv", ".tsv"}

# ============================================================================
# Validation Patterns
# ============================================================================

# Email pattern
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# Area/hectares pattern
HECTARES_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:ha|hectares?)", re.IGNORECASE)

# Percentage pattern
PERCENTAGE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*%")

# ============================================================================
# Helper Functions
# ============================================================================


def match_any(text: str, patterns: list[re.Pattern]) -> bool:
    """Check if text matches any of the given patterns.

    Args:
        text: Text to match
        patterns: List of compiled regex patterns

        Returns:
        True if any pattern matches, False otherwise
    """
    return any(pattern.search(text) for pattern in patterns)


def extract_all_dates(text: str) -> list[str]:
    """Extract all dates from text.

    Args:
        text: Text to search

    Returns:
        List of date strings found
    """
    dates = []
    dates.extend(DATE_ISO.findall(text))
    dates.extend(DATE_SLASH.findall(text))
    dates.extend(DATE_WRITTEN.findall(text))
    return dates


def extract_project_ids(text: str) -> list[str]:
    """Extract all project IDs from text.

    Args:
        text: Text to search

    Returns:
        List of project ID strings found
    """
    return PROJECT_ID_PATTERN.findall(text)


def is_gis_file(filename: str) -> bool:
    """Check if filename is a GIS file.

    Args:
        filename: Name of file

    Returns:
        True if GIS file, False otherwise
    """
    from pathlib import Path

    return Path(filename).suffix.lower() in GIS_EXTENSIONS


def is_image_file(filename: str) -> bool:
    """Check if filename is an image file.

    Args:
        filename: Name of file

    Returns:
        True if image file, False otherwise
    """
    from pathlib import Path

    return Path(filename).suffix.lower() in IMAGE_EXTENSIONS


def is_pdf_file(filename: str) -> bool:
    """Check if filename is a PDF file.

    Args:
        filename: Name of file

    Returns:
        True if PDF file, False otherwise
    """
    from pathlib import Path

    return Path(filename).suffix.lower() in PDF_EXTENSION


def is_spreadsheet_file(filename: str) -> bool:
    """Check if filename is a spreadsheet file.

    Args:
        filename: Name of file

    Returns:
        True if spreadsheet file, False otherwise
    """
    from pathlib import Path

    return Path(filename).suffix.lower() in SPREADSHEET_EXTENSIONS
