"""
Test script for the updated recommendation engine with real JoSAA data.
"""
import sys
sys.path.insert(0, '.')

from engines.recommendation import recommend, validate_cutoffs

# Validate cutoffs
print("="*80)
print("Validating cutoff ranks...")
print("="*80)
validate_cutoffs()

# Test 1: JEE Advanced rank 2300 (should NOT see IIT Bombay CS)
print("\n" + "="*80)
print("Test 1: JEE Advanced rank 2300, CS branch")
print("="*80)
recs = recommend(student_rank=2300, branch="CS", rank_type="jee_advanced", max_results_per_tier=3)
print(f"\nTotal recommendations: {len(recs)}")
for rec in recs[:10]:
    print(f"  [{rec.recommendation_tier:8}] {rec.name:30} {rec.branch:10} Cutoff: {rec.cutoff_rank:6} (Gap: {rec.rank_gap:+6})")

# Check if IIT Bombay CS is in the list
iitb_cs = [r for r in recs if "IIT Bombay" in r.name and r.branch == "CS"]
if iitb_cs:
    print(f"\n❌ FAIL: IIT Bombay CS should NOT appear for rank 2300 (cutoff ~65)")
else:
    print(f"\n✅ PASS: IIT Bombay CS correctly excluded for rank 2300")

# Test 2: JEE Main rank 3000 (should see NIT Trichy CS as Dream/Moderate)
print("\n" + "="*80)
print("Test 2: JEE Main rank 3000, CS branch")
print("="*80)
recs = recommend(student_rank=3000, branch="CS", rank_type="jee_main", max_results_per_tier=3)
print(f"\nTotal recommendations: {len(recs)}")
for rec in recs[:10]:
    print(f"  [{rec.recommendation_tier:8}] {rec.name:30} {rec.branch:10} Cutoff: {rec.cutoff_rank:6} (Gap: {rec.rank_gap:+6})")

# Check if NIT Trichy CS is in the list
nit_trichy_cs = [r for r in recs if "NIT Trichy" in r.name and r.branch == "CS"]
if nit_trichy_cs:
    print(f"\n✅ PASS: NIT Trichy CS found (cutoff: {nit_trichy_cs[0].cutoff_rank}, tier: {nit_trichy_cs[0].recommendation_tier})")
else:
    print(f"\n❌ FAIL: NIT Trichy CS should appear for JEE Main rank 3000")

# Test 3: JEE Advanced rank 100 (should see IIT Bombay CS as Moderate/Safe)
print("\n" + "="*80)
print("Test 3: JEE Advanced rank 100, CS branch")
print("="*80)
recs = recommend(student_rank=100, branch="CS", rank_type="jee_advanced", max_results_per_tier=3)
print(f"\nTotal recommendations: {len(recs)}")
for rec in recs[:10]:
    print(f"  [{rec.recommendation_tier:8}] {rec.name:30} {rec.branch:10} Cutoff: {rec.cutoff_rank:6} (Gap: {rec.rank_gap:+6})")

# Check if IIT Bombay CS is in the list
iitb_cs = [r for r in recs if "IIT Bombay" in r.name and r.branch == "CS"]
if iitb_cs:
    print(f"\n✅ PASS: IIT Bombay CS found (cutoff: {iitb_cs[0].cutoff_rank}, tier: {iitb_cs[0].recommendation_tier})")
    if iitb_cs[0].recommendation_tier in ["Moderate", "Safe"]:
        print(f"✅ PASS: Correctly classified as {iitb_cs[0].recommendation_tier} for rank 100")
    else:
        print(f"❌ FAIL: Should be Moderate/Safe, not {iitb_cs[0].recommendation_tier}")
else:
    print(f"\n❌ FAIL: IIT Bombay CS should appear for rank 100")

print("\n" + "="*80)
print("All tests complete!")
print("="*80)
