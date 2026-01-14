#!/usr/bin/env python3
"""Run accuracy test against Botany Farm ground truth using Gemini."""

import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from registry_review_mcp.extractors.llm_extractors import (
    DateExtractor,
    LandTenureExtractor,
    ProjectIDExtractor,
)

# Load ground truth
GROUND_TRUTH_PATH = Path("tests/botany_farm_ground_truth.json")
with open(GROUND_TRUTH_PATH) as f:
    GROUND_TRUTH = json.load(f)

async def main():
    print("="*60)
    print("BOTANY FARM ACCURACY TEST - GEMINI 3 FLASH")
    print("="*60)
    
    # Load all markdown documents
    doc_dir = Path("examples/22-23/22-23")
    docs = {}
    for md_file in doc_dir.glob("*.md"):
        docs[md_file.stem] = md_file.read_text()[:50000]  # First 50K chars
        print(f"Loaded: {md_file.name} ({len(docs[md_file.stem]):,} chars)")
    
    print()
    
    # ===== DATE EXTRACTION =====
    print("\n" + "="*60)
    print("DATE EXTRACTION")
    print("="*60)
    
    date_extractor = DateExtractor()
    all_dates = []
    
    for doc_name, content in docs.items():
        print(f"\nExtracting dates from {doc_name}...")
        results = await date_extractor.extract(content, [], doc_name)
        all_dates.extend(results)
        for r in results:
            print(f"  {r.field_type}: {r.value} (conf: {r.confidence:.2f})")
    
    # Compare with ground truth
    print("\n--- Ground Truth Comparison ---")
    ground_truth_dates = {d["field_type"]: d["value"] for d in GROUND_TRUTH["ground_truth"]["dates"]}
    extracted_types = {f.field_type for f in all_dates}

    matches = 0
    for gt_type, gt_value in ground_truth_dates.items():
        extracted = [f for f in all_dates if f.field_type == gt_type]
        if extracted:
            # Check if ANY extracted value matches (not just first one)
            found_match = False
            for ext in extracted:
                extracted_value = str(ext.value)
                if gt_value in extracted_value or extracted_value in gt_value:
                    print(f"  ✓ {gt_type}: {gt_value} == {extracted_value}")
                    matches += 1
                    found_match = True
                    break
            if not found_match:
                # Show all extracted values for debugging
                all_values = [str(e.value) for e in extracted]
                print(f"  ✗ {gt_type}: expected {gt_value}, got {all_values}")
        else:
            print(f"  ✗ {gt_type}: NOT FOUND (expected {gt_value})")
    
    date_accuracy = matches / len(ground_truth_dates) if ground_truth_dates else 0
    print(f"\nDate Accuracy: {matches}/{len(ground_truth_dates)} ({date_accuracy:.0%})")
    
    # ===== LAND TENURE EXTRACTION =====
    print("\n" + "="*60)
    print("LAND TENURE EXTRACTION")
    print("="*60)
    
    tenure_extractor = LandTenureExtractor()
    all_tenure = []
    
    for doc_name, content in docs.items():
        if "Project_Plan" in doc_name or "Baseline" in doc_name:  # Focus on key docs
            print(f"\nExtracting tenure from {doc_name}...")
            results = await tenure_extractor.extract(content, [], doc_name)
            all_tenure.extend(results)
            for r in results:
                print(f"  {r.field_type}: {r.value} (conf: {r.confidence:.2f})")
    
    # Compare with ground truth
    print("\n--- Ground Truth Comparison ---")
    gt_tenure = GROUND_TRUTH["ground_truth"]["land_tenure"][0]
    acceptable_names = GROUND_TRUTH["acceptable_variations"]["owner_name"]
    
    owner_found = False
    owner_names = [f for f in all_tenure if f.field_type == "owner_name"]
    if owner_names:
        for owner in owner_names:
            if any(name in str(owner.value) or str(owner.value) in name for name in acceptable_names):
                print(f"  ✓ owner_name: {owner.value}")
                owner_found = True
                break
        if not owner_found:
            print(f"  ✗ owner_name: {owner_names[0].value} not in {acceptable_names}")
    else:
        print(f"  ✗ owner_name: NOT FOUND")
    
    areas = [f for f in all_tenure if f.field_type == "area_hectares"]
    area_found = False
    if areas:
        for area in areas:
            try:
                extracted_area = float(area.value)
                expected_area = gt_tenure["area_hectares"]
                if abs(extracted_area - expected_area) / expected_area < 0.05:  # 5% tolerance
                    print(f"  ✓ area_hectares: {extracted_area} (expected {expected_area})")
                    area_found = True
                    break
            except:
                pass
        if not area_found:
            print(f"  ✗ area_hectares: {areas[0].value} != {gt_tenure['area_hectares']}")
    else:
        print(f"  ✗ area_hectares: NOT FOUND")
    
    tenure_accuracy = ((1 if owner_found else 0) + (1 if area_found else 0)) / 2
    print(f"\nTenure Accuracy: {int(owner_found) + int(area_found)}/2 ({tenure_accuracy:.0%})")
    
    # ===== PROJECT ID EXTRACTION =====
    print("\n" + "="*60)
    print("PROJECT ID EXTRACTION")
    print("="*60)
    
    id_extractor = ProjectIDExtractor()
    all_ids = []
    
    for doc_name, content in docs.items():
        print(f"\nExtracting IDs from {doc_name}...")
        results = await id_extractor.extract(content, [], doc_name)
        all_ids.extend(results)
        unique_ids = set(r.value for r in results)
        if unique_ids:
            print(f"  Found: {unique_ids}")
    
    # Compare with ground truth
    print("\n--- Ground Truth Comparison ---")
    gt_ids = {pid["value"] for pid in GROUND_TRUTH["ground_truth"]["project_ids"]}
    extracted_ids = set(f.value for f in all_ids)
    
    matches = gt_ids & extracted_ids
    for pid in gt_ids:
        if pid in extracted_ids:
            print(f"  ✓ {pid}")
        else:
            print(f"  ✗ {pid}: NOT FOUND")
    
    id_accuracy = len(matches) / len(gt_ids) if gt_ids else 0
    print(f"\nProject ID Accuracy: {len(matches)}/{len(gt_ids)} ({id_accuracy:.0%})")
    
    # ===== SUMMARY =====
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Date Extraction:     {date_accuracy:.0%}")
    print(f"Land Tenure:         {tenure_accuracy:.0%}")
    print(f"Project IDs:         {id_accuracy:.0%}")
    overall = (date_accuracy + tenure_accuracy + id_accuracy) / 3
    print(f"Overall Accuracy:    {overall:.0%}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
