"""
run_pipeline.py
===============
One-click runner:
  Drop raw files into satti_group_raw_data/ → run this → get Satti_Group_Report.xlsx

Usage:
  python run_pipeline.py
"""

import time

print("=" * 60)
print("  SATTI GROUP – Data Pipeline")
print("  Messy Excel → Clean → Match → Analyze → Report")
print("=" * 60)

t0 = time.time()

import step1_clean
import step2_match_analyze
import step3_report

# Step 1
step1_clean.run()

# Step 2
step2_match_analyze.run()

# Step 3
step3_report.run()

print(f"Total time: {time.time()-t0:.1f}s")
print("\nReport ready: Satti_Group_Report.xlsx")
