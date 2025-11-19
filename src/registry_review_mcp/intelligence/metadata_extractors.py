"""Intelligent metadata extraction from documents.

Extracts project context from filenames and document content:
- Project IDs (e.g., C06-4997, C02-1234)
- Crediting periods (e.g., 2022-2032)
- Methodology versions (e.g., Soil Carbon v1.2.2)
- Document dates and versions
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extract structured metadata from documents."""

    # Patterns for common metadata
    PROJECT_ID_PATTERNS = [
        r'(C\d{2}-\d{4,5})',  # C06-4997, C02-12345 (no word boundaries due to dash)
        r'\b(VCS\d{4,5})\b',  # VCS1234
        r'\b(GS\d{4,5})\b',  # GS1234
    ]

    METHODOLOGY_PATTERNS = [
        r'Soil\s+Carbon\s+(?:Methodology\s+)?v?(\d+\.\d+(?:\.\d+)?)',
        r'Grassland\s+(?:Methodology\s+)?(?:Version\s+)?v?(\d+\.\d+(?:\.\d+)?)',
        r'Methodology\s+(?:Version\s+)?v?(\d+\.\d+(?:\.\d+)?)',
    ]

    YEAR_RANGE_PATTERNS = [
        r'(\d{4})\s*[-–—]\s*(\d{4})',  # 2022-2032, 2022–2032
        r'crediting\s+period[:\s]+(\d{4})\s*[-–—]\s*(\d{4})',
    ]

    VERSION_PATTERNS = [
        r'[vV]ersion\s+(\d+(?:\.\d+)*)',
        r'\bv(\d+(?:\.\d+)+)\b',
        r'_v(\d+(?:\.\d+)+)',
    ]

    def __init__(self):
        """Initialize metadata extractor."""
        self.compiled_patterns = {
            'project_id': [re.compile(p, re.IGNORECASE) for p in self.PROJECT_ID_PATTERNS],
            'methodology': [re.compile(p, re.IGNORECASE) for p in self.METHODOLOGY_PATTERNS],
            'year_range': [re.compile(p, re.IGNORECASE) for p in self.YEAR_RANGE_PATTERNS],
            'version': [re.compile(p, re.IGNORECASE) for p in self.VERSION_PATTERNS],
        }

    def extract_project_id(self, text: str, filename: str = "") -> dict[str, Any]:
        """Extract project ID with confidence scoring.

        Args:
            text: Document text (first few pages usually sufficient)
            filename: Document filename

        Returns:
            Dictionary with:
                - project_id: str | None
                - confidence: float (0.0-1.0)
                - sources: list[str] - Where ID was found
                - occurrences: int - How many times found
        """
        sources = []
        found_ids = []

        # Search filename first
        if filename:
            for pattern in self.compiled_patterns['project_id']:
                matches = pattern.findall(filename)
                if matches:
                    found_ids.extend(matches)
                    sources.append(f"filename: {filename}")

        # Search text (first 5000 chars usually sufficient)
        if text:  # Only search if text is not empty
            search_text = text[:5000] if len(text) > 5000 else text
            for pattern in self.compiled_patterns['project_id']:
                matches = pattern.findall(search_text)
                if matches:
                    found_ids.extend(matches)
                    sources.append("document content")

        if not found_ids:
            return {
                "project_id": None,
                "confidence": 0.0,
                "sources": [],
                "occurrences": 0,
            }

        # Find most common ID (in case of multiple)
        from collections import Counter
        id_counts = Counter(found_ids)
        most_common_id, occurrences = id_counts.most_common(1)[0]

        # Calculate confidence
        # High confidence if:
        # - Found in multiple places (filename + content)
        # - Found multiple times
        # - Only one unique ID found
        confidence = 0.5  # Base

        if len(id_counts) == 1:
            confidence += 0.3  # Only one ID (no conflicts)

        if occurrences >= 3:
            confidence += 0.2  # Found multiple times
        elif occurrences >= 2:
            confidence += 0.1

        if len(sources) >= 2:
            confidence += 0.2  # Found in multiple sources

        confidence = min(confidence, 1.0)

        return {
            "project_id": most_common_id,
            "confidence": round(confidence, 2),
            "sources": list(set(sources)),
            "occurrences": occurrences,
        }

    def extract_crediting_period(self, text: str, filename: str = "") -> dict[str, Any]:
        """Extract crediting period (year range).

        Args:
            text: Document text
            filename: Document filename

        Returns:
            Dictionary with:
                - start_year: int | None
                - end_year: int | None
                - period_string: str | None (e.g., "2022-2032")
                - confidence: float
                - sources: list[str]
        """
        sources = []
        year_ranges = []

        # Search filename
        if filename:
            for pattern in self.compiled_patterns['year_range']:
                matches = pattern.findall(filename)
                for match in matches:
                    if isinstance(match, tuple):
                        year_ranges.append(match)
                        sources.append(f"filename: {filename}")

        # Search text (first 10000 chars)
        search_text = text[:10000] if len(text) > 10000 else text
        for pattern in self.compiled_patterns['year_range']:
            matches = pattern.findall(search_text)
            for match in matches:
                if isinstance(match, tuple):
                    year_ranges.append(match)
                    sources.append("document content")

        if not year_ranges:
            return {
                "start_year": None,
                "end_year": None,
                "period_string": None,
                "confidence": 0.0,
                "sources": [],
            }

        # Find most common year range
        from collections import Counter
        range_counts = Counter(year_ranges)
        most_common_range, occurrences = range_counts.most_common(1)[0]
        start_year, end_year = int(most_common_range[0]), int(most_common_range[1])

        # Validate year range makes sense
        current_year = datetime.now().year
        if not (1990 <= start_year <= current_year + 50):
            return {
                "start_year": None,
                "end_year": None,
                "period_string": None,
                "confidence": 0.0,
                "sources": [],
            }

        if end_year <= start_year or end_year > current_year + 50:
            # Invalid range
            confidence = 0.3  # Low confidence for invalid range
        else:
            # Calculate confidence
            confidence = 0.5  # Base

            if len(range_counts) == 1:
                confidence += 0.2  # Only one range found

            if occurrences >= 2:
                confidence += 0.2  # Found multiple times

            if len(sources) >= 2:
                confidence += 0.1  # Found in multiple sources

            confidence = min(confidence, 1.0)

        return {
            "start_year": start_year,
            "end_year": end_year,
            "period_string": f"{start_year}-{end_year}",
            "confidence": round(confidence, 2),
            "sources": list(set(sources)),
            "duration_years": end_year - start_year,
        }

    def extract_methodology(self, text: str, filename: str = "") -> dict[str, Any]:
        """Extract methodology name and version.

        Args:
            text: Document text
            filename: Document filename

        Returns:
            Dictionary with:
                - methodology_name: str | None
                - version: str | None
                - full_string: str | None (e.g., "Soil Carbon v1.2.2")
                - confidence: float
                - sources: list[str]
        """
        sources = []
        methodologies = []

        # Search text (first 5000 chars - methodology usually stated early)
        search_text = text[:5000] if len(text) > 5000 else text

        for pattern in self.compiled_patterns['methodology']:
            matches = pattern.finditer(search_text)
            for match in matches:
                full_text = match.group(0)
                version = match.group(1) if match.groups() else None

                # Determine methodology name
                if 'soil' in full_text.lower():
                    name = "Soil Carbon"
                elif 'grassland' in full_text.lower():
                    name = "Grassland"
                else:
                    name = "Unknown"

                methodologies.append({
                    "name": name,
                    "version": version,
                    "full_text": full_text,
                })
                sources.append("document content")

        if not methodologies:
            return {
                "methodology_name": None,
                "version": None,
                "full_string": None,
                "confidence": 0.0,
                "sources": [],
            }

        # Use first found (usually most prominent)
        primary = methodologies[0]

        # Calculate confidence
        confidence = 0.6  # Base (methodology usually explicit)

        if len(methodologies) >= 2:
            # Found multiple times
            confidence += 0.2

        if primary["version"]:
            # Has version number
            confidence += 0.2

        confidence = min(confidence, 1.0)

        full_string = f"{primary['name']} v{primary['version']}" if primary['version'] else primary['name']

        return {
            "methodology_name": primary["name"],
            "version": primary["version"],
            "full_string": full_string,
            "confidence": round(confidence, 2),
            "sources": list(set(sources)),
            "occurrences": len(methodologies),
        }

    def extract_document_version(self, filename: str) -> dict[str, Any]:
        """Extract document version from filename.

        Args:
            filename: Document filename

        Returns:
            Dictionary with:
                - version: str | None
                - confidence: float
        """
        for pattern in self.compiled_patterns['version']:
            match = pattern.search(filename)
            if match:
                version = match.group(1)
                return {
                    "version": version,
                    "confidence": 0.9,  # High confidence from filename
                }

        return {
            "version": None,
            "confidence": 0.0,
        }

    def extract_all_metadata(
        self,
        text: str,
        filename: str = "",
    ) -> dict[str, Any]:
        """Extract all metadata from document.

        Args:
            text: Document text
            filename: Document filename

        Returns:
            Comprehensive metadata dictionary
        """
        return {
            "project_id": self.extract_project_id(text, filename),
            "crediting_period": self.extract_crediting_period(text, filename),
            "methodology": self.extract_methodology(text, filename),
            "document_version": self.extract_document_version(filename),
            "extracted_at": datetime.now().isoformat(),
        }


# Singleton instance
_metadata_extractor = None


def get_metadata_extractor() -> MetadataExtractor:
    """Get singleton metadata extractor instance."""
    global _metadata_extractor
    if _metadata_extractor is None:
        _metadata_extractor = MetadataExtractor()
    return _metadata_extractor
