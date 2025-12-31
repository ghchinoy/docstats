# Copyright 2025 Google LLC
# baseline_analysis.py - Generates baseline scores for the Golden Set.

import asyncio
import os
import json
from metrics import calculate_readability_metrics_logic

SAMPLES = [
    "level_primary.txt",
    "level_middle.txt",
    "level_academic.txt",
    "level_legal.txt"
]

async def run_baseline():
    results = {}
    print(f"{ 'Sample':<20} | {'Grade Standard':<20} | {'Word Count':<10}")
    print("-" * 55)
    
    for filename in SAMPLES:
        path = os.path.join("samples", filename)
        with open(path, "r") as f:
            text = f.read()
        
        scores = await calculate_readability_metrics_logic(text, filename)
        results[filename] = scores.model_dump()
        
        print(f"{filename:<20} | {scores.text_standard:<20} | {scores.word_count:<10}")

    with open("samples/baseline_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nFull results saved to samples/baseline_results.json")

if __name__ == "__main__":
    asyncio.run(run_baseline())

