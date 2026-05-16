"""
Test script to verify JEE Advanced only returns IITs, not NITs
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from engines.recommendation import recommend

print("=" * 80)
print("TEST 1: JEE Advanced rank 2300, CS branch")
print("Expected: Only IITs, NO NITs")
print("=" * 80)

recs = recommend(
    student_rank=2300,
    branch="CS",
    rank_type="jee_advanced",
    max_results_per_tier=5
)

print(f"\nTotal recommendations: {len(recs)}")
print("\nColleges returned:")
for i, rec in enumerate(recs, 1):
    print(f"{i}. {rec.name} - {rec.branch} - {rec.recommendation_tier}")
    print(f"   Cutoff: {rec.cutoff_rank}, Rank Type: {rec.rank_type}")

# Check for NITs
nits_found = [r for r in recs if 'NIT' in r.name and 'IIIT' not in r.name]
iits_found = [r for r in recs if 'IIT' in r.name]

print(f"\n{'='*80}")
print(f"VALIDATION RESULTS:")
print(f"{'='*80}")
print(f"IITs found: {len(iits_found)}")
print(f"NITs found: {len(nits_found)}")

if nits_found:
    print(f"\n❌ FAILED: Found {len(nits_found)} NITs in JEE Advanced results!")
    for nit in nits_found:
        print(f"   - {nit.name}")
else:
    print(f"\n✅ PASSED: No NITs found in JEE Advanced results")

print("\n" + "=" * 80)
print("TEST 2: JEE Main rank 5000, CS branch")
print("Expected: NITs, IIITs, GFTIs - NO IITs")
print("=" * 80)

recs_main = recommend(
    student_rank=5000,
    branch="CS",
    rank_type="jee_main",
    max_results_per_tier=5
)

print(f"\nTotal recommendations: {len(recs_main)}")
print("\nColleges returned:")
for i, rec in enumerate(recs_main[:10], 1):
    print(f"{i}. {rec.name} - {rec.branch} - {rec.recommendation_tier}")
    print(f"   Cutoff: {rec.cutoff_rank}, Rank Type: {rec.rank_type}")

# Check for IITs (should not be there for JEE Main)
iits_in_main = [r for r in recs_main if 'IIT' in r.name and 'IIIT' not in r.name]
nits_in_main = [r for r in recs_main if 'NIT' in r.name]

print(f"\n{'='*80}")
print(f"VALIDATION RESULTS:")
print(f"{'='*80}")
print(f"NITs found: {len(nits_in_main)}")
print(f"IITs found: {len(iits_in_main)}")

if iits_in_main:
    print(f"\n❌ FAILED: Found {len(iits_in_main)} IITs in JEE Main results!")
    for iit in iits_in_main:
        print(f"   - {iit.name}")
else:
    print(f"\n✅ PASSED: No IITs found in JEE Main results")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
if not nits_found and not iits_in_main:
    print("✅ ALL TESTS PASSED: Exam type filtering is working correctly!")
else:
    print("❌ TESTS FAILED: Exam type filtering needs fixing")
