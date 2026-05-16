"""
Test script for India-specific entity extractor.
Tests extraction of colleges, branches, exams, ranks, locations, and budget.
"""
import sys
sys.path.insert(0, '.')

from nlp.entities.extractor import EntityExtractor


def test_entity_extractor():
    """Test the India-specific entity extractor."""
    print("="*80)
    print("Testing India-Specific Entity Extractor")
    print("="*80)
    
    extractor = EntityExtractor()
    
    test_cases = [
        # Test case 1: Acceptance criterion 1
        {
            "query": "I got 2300 rank in JEE Advanced, want CSE at IIT Bombay",
            "expected": {
                "ranks": [2300],
                "exams": ["JEE Advanced"],
                "branches": ["CSE"],
                "colleges": ["IIT Bombay"]
            }
        },
        
        # Test case 2: Acceptance criterion 2
        {
            "query": "budget is around 3 lakh per year, prefer south India",
            "expected": {
                "budget_lakh": 3.0,
                "locations": ["south India"]
            }
        },
        
        # Test case 3: Short forms
        {
            "query": "Got admission in IITB for ECE",
            "expected": {
                "colleges": ["IIT Bombay"],
                "branches": ["ECE"]
            }
        },
        
        # Test case 4: Multiple entities
        {
            "query": "JEE Main rank 5000, want CS or IT at NIT Trichy or NIT Surathkal",
            "expected": {
                "ranks": [5000],
                "exams": ["JEE Main"],
                "branches": ["CS", "IT"],
                "colleges": ["NIT Trichy", "NIT Surathkal"]
            }
        },
        
        # Test case 5: Budget in rupees
        {
            "query": "Can afford ₹2,00,000 per year",
            "expected": {
                "budget_lakh": 2.0
            }
        },
        
        # Test case 6: Rank in 'k' format
        {
            "query": "My rank is 2.3k in NEET",
            "expected": {
                "ranks": [2300],
                "exams": ["NEET"]
            }
        },
        
        # Test case 7: Multiple locations
        {
            "query": "Prefer colleges in Bangalore, Pune, or Maharashtra",
            "expected": {
                "locations": ["Bangalore", "Pune", "Maharashtra"]
            }
        },
        
        # Test case 8: State exams
        {
            "query": "Got 15000 rank in KCET, want Mechanical engineering",
            "expected": {
                "ranks": [15000],
                "exams": ["KCET"],
                "branches": ["Mechanical"]
            }
        },
        
        # Test case 9: Private exams
        {
            "query": "BITSAT score 320, interested in BITS Pilani CS",
            "expected": {
                "exams": ["BITSAT"],
                "colleges": ["BITS Pilani"],
                "branches": ["CS"]
            }
        },
        
        # Test case 10: Complex query
        {
            "query": "I got AIR 1500 in JEE Advanced. Budget is 2 lakh. Want CSE or ECE at IIT Delhi, IIT Madras, or IIIT Hyderabad. Prefer North India.",
            "expected": {
                "ranks": [1500],
                "exams": ["JEE Advanced"],
                "budget_lakh": 2.0,
                "branches": ["CSE", "ECE"],
                "colleges": ["IIT Delhi", "IIT Madras", "IIIT Hyderabad"],
                "locations": ["North India"]
            }
        },
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Test Case {i}")
        print(f"{'='*80}")
        print(f"Query: {test['query']}")
        print(f"\nExpected:")
        for key, value in test['expected'].items():
            print(f"  {key}: {value}")
        
        result = extractor.extract(test['query'])
        
        print(f"\nActual:")
        for key, value in result.items():
            if value:  # Only print non-empty values
                print(f"  {key}: {value}")
        
        # Check if expected values are present
        test_passed = True
        for key, expected_value in test['expected'].items():
            actual_value = result.get(key)
            
            if isinstance(expected_value, list):
                # Check if all expected items are in actual
                missing = [item for item in expected_value if item not in actual_value]
                if missing:
                    print(f"\n❌ FAIL: Missing {key}: {missing}")
                    test_passed = False
                else:
                    print(f"✅ {key}: All expected items found")
            elif isinstance(expected_value, (int, float)):
                if actual_value != expected_value:
                    print(f"\n❌ FAIL: {key} mismatch. Expected: {expected_value}, Got: {actual_value}")
                    test_passed = False
                else:
                    print(f"✅ {key}: {actual_value}")
            else:
                if actual_value != expected_value:
                    print(f"\n❌ FAIL: {key} mismatch. Expected: {expected_value}, Got: {actual_value}")
                    test_passed = False
                else:
                    print(f"✅ {key}: {actual_value}")
        
        if test_passed:
            print(f"\n✅ Test Case {i} PASSED")
            passed += 1
        else:
            print(f"\n❌ Test Case {i} FAILED")
            failed += 1
    
    print(f"\n{'='*80}")
    print(f"Test Summary")
    print(f"{'='*80}")
    print(f"Total: {len(test_cases)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print(f"\n✅ ALL TESTS PASSED!")
    else:
        print(f"\n❌ {failed} TEST(S) FAILED")
    
    return failed == 0


def test_acceptance_criteria():
    """Test the specific acceptance criteria."""
    print("\n" + "="*80)
    print("Testing Acceptance Criteria")
    print("="*80)
    
    extractor = EntityExtractor()
    
    # Criterion 1
    print("\n✓ Criterion 1: Extract rank, exam, branch, and college")
    query1 = "I got 2300 rank in JEE Advanced, want CSE at IIT Bombay"
    result1 = extractor.extract(query1)
    print(f"Query: {query1}")
    print(f"Result: {result1}")
    
    if (2300 in result1['ranks'] and 
        any('JEE Advanced' in e for e in result1['exams']) and
        'CSE' in result1['branches'] and
        'IIT Bombay' in result1['colleges']):
        print("✅ PASS: All entities correctly extracted")
    else:
        print("❌ FAIL: Missing expected entities")
    
    # Criterion 2
    print("\n✓ Criterion 2: Extract budget and location")
    query2 = "budget is around 3 lakh per year, prefer south India"
    result2 = extractor.extract(query2)
    print(f"Query: {query2}")
    print(f"Result: {result2}")
    
    if (result2['budget_lakh'] == 3.0 and
        any('south india' in loc.lower() for loc in result2['locations'])):
        print("✅ PASS: Budget and location correctly extracted")
    else:
        print("❌ FAIL: Budget or location extraction failed")
    
    print("\n" + "="*80)
    print("✅ Acceptance Criteria Tests Complete")
    print("="*80)


def test_college_loading():
    """Test that colleges are loaded from JSON."""
    print("\n" + "="*80)
    print("Testing College Loading")
    print("="*80)
    
    from nlp.entities.extractor import KNOWN_COLLEGES, COLLEGE_SHORT_FORMS
    
    print(f"\nLoaded {len(KNOWN_COLLEGES)} colleges")
    print(f"Sample colleges: {KNOWN_COLLEGES[:10]}")
    print(f"\nShort form mappings: {len(COLLEGE_SHORT_FORMS)} colleges")
    print(f"Sample mappings:")
    for college, shorts in list(COLLEGE_SHORT_FORMS.items())[:5]:
        print(f"  {college}: {shorts}")
    
    if len(KNOWN_COLLEGES) > 100:
        print("\n✅ PASS: Colleges loaded from JSON (>100 colleges)")
    else:
        print("\n⚠️  WARNING: Only loaded fallback colleges")
    
    print("="*80)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("India-Specific Entity Extractor Test Suite")
    print("="*80)
    
    # Test college loading
    test_college_loading()
    
    # Run main tests
    success = test_entity_extractor()
    
    # Test acceptance criteria
    test_acceptance_criteria()
    
    print("\n" + "="*80)
    if success:
        print("✅ ALL TESTS COMPLETE - SUCCESS")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*80)
    
    sys.exit(0 if success else 1)
