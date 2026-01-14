#!/usr/bin/env python3
"""Convert all 7 Botany Farm PDFs to markdown."""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from registry_review_mcp.extractors.fast_extractor import batch_fast_extract_pdfs

async def main():
    pdf_dir = Path("examples/22-23/22-23")
    pdfs = list(pdf_dir.glob("*.pdf"))
    
    print(f"Found {len(pdfs)} PDFs to convert:")
    for pdf in pdfs:
        print(f"  - {pdf.name}")
    print()
    
    # Convert all PDFs
    results = await batch_fast_extract_pdfs([str(p) for p in pdfs])
    
    print(f"\n=== Saving Markdown Files ===")
    for filepath, result in results.items():
        if result.get("success", True):
            # Save markdown to file
            md_path = Path(filepath).with_suffix(".md")
            markdown = result.get("markdown", "")
            if markdown:
                md_path.write_text(markdown)
                print(f"✓ {md_path.name}: {len(markdown):,} chars")
            else:
                print(f"✗ {Path(filepath).name}: No markdown generated")
        else:
            print(f"✗ {Path(filepath).name}: {result.get('error', 'Unknown error')}")
    
    # List generated markdown files
    print(f"\n=== All Markdown Files ===")
    for md in sorted(pdf_dir.glob("*.md")):
        print(f"  {md.name}: {md.stat().st_size:,} bytes")

if __name__ == "__main__":
    asyncio.run(main())
