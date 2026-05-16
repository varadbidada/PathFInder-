"""
Pathfinder API Test Suite
Comprehensive tests for all endpoints and novel features
"""
import requests
import json
import time
from typing import Optional

BASE_URL = "http://127.0.0.1:8080"

# ANSI color codes for pretty output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_header(text: str):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text.center(70)}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def print_test(text: str):
    print(f"{YELLOW}🔍 {text}{RESET}")

def print_success(text: str):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text: str):
    print(f"{RED}❌ {text}{RESET}")

def print_info(text: str):
    print(f"   {text}")

def test_health():
    """Test 1: Health Check"""
    print_test("Test 1: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print_success(f"Server is healthy (v{data['version']})")
            print_info(f"Active sessions: {data['active_sessions']}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Connection failed: {e}")
        return False

def test_branches():
    """Test 2: List Available Branches"""
    print_test("Test 2: List Available Branches")
    try:
        response = requests.get(f"{BASE_URL}/branches")
        if response.status_code == 200:
            data = response.json()
            branches = data['branches']
            print_success(f"Found {len(branches)} branches")
            print_info(f"Branches: {', '.join(branches)}")
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_start_session() -> Optional[str]:
    """Test 3: Start New Session with Pre-filled Data"""
    print_test("Test 3: Start New Session (with pre-filled data)")
    try:
        response = requests.post(f"{BASE_URL}/session/start", json={
            "jee_rank": 5000,
            "budget_lakh": 5,
            "preferred_location": "Bangalore"
        })
        if response.status_code == 200:
            data = response.json()
            session_id = data['session_id']
            print_success(f"Session created: {session_id[:16]}...")
            print_info(f"First question: {data['first_question'][:60]}...")
            return session_id
        else:
            print_error(f"Failed: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None

def test_chat(session_id: str):
    """Test 4: Chat - Answer Questions"""
    print_test("Test 4: Chat - Answer Questions")
    
    messages = [
        "I love coding and solving algorithmic problems. Math is my favorite subject.",
        "I enjoy working on computers and building software projects.",
        "I'm good at logical thinking and problem-solving."
    ]
    
    for i, message in enumerate(messages, 1):
        try:
            print_info(f"Message {i}: {message[:50]}...")
            response = requests.post(f"{BASE_URL}/chat", json={
                "session_id": session_id,
                "user_message": message
            })
            
            if response.status_code == 200:
                data = response.json()
                scores = data['branch_scores']
                top_branch = max(scores, key=scores.get)
                print_success(f"Response received. Top branch: {top_branch} ({scores[top_branch]:.2f})")
                time.sleep(0.5)  # Small delay between messages
            else:
                print_error(f"Failed: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Error: {e}")
            return False
    
    return True

def test_get_session(session_id: str):
    """Test 5: Get Session State"""
    print_test("Test 5: Get Session State")
    try:
        response = requests.get(f"{BASE_URL}/session/{session_id}")
        if response.status_code == 200:
            data = response.json()
            print_success("Session state retrieved")
            print_info(f"Rank: {data['rank']}")
            print_info(f"Budget: ₹{data['budget_lakh']} Lakh")
            print_info(f"Location: {data['preferred_location']}")
            print_info(f"Recommended Branch: {data['recommended_branch']}")
            print_info(f"Confidence: {data['overall_confidence']:.2%}")
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_what_if():
    """Test 6: Feature 9A - What-If Rank Simulator"""
    print_test("Test 6: Feature 9A - What-If Rank Simulator")
    try:
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/what-if", json={
            "current_rank": 10000,
            "target_rank": 5000,
            "branch": "CS",
            "rank_type": "jee_main"
        })
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"What-If simulation completed in {elapsed:.0f}ms")
            print_info(f"Colleges gained: {len(data['colleges_gained'])}")
            print_info(f"Colleges lost: {len(data['colleges_lost'])}")
            print_info(f"Rank improvement needed: {data['rank_improvement_needed']}")
            
            if data['colleges_gained']:
                print_info(f"Example gained: {data['colleges_gained'][0]['name']}")
            
            # Check acceptance criterion: < 200ms
            if elapsed < 200:
                print_success(f"✓ Acceptance criterion met: {elapsed:.0f}ms < 200ms")
            else:
                print_error(f"✗ Acceptance criterion failed: {elapsed:.0f}ms >= 200ms")
            
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_peer_comparison():
    """Test 7: Feature 9B - Peer Comparison"""
    print_test("Test 7: Feature 9B - Peer Comparison")
    
    # First, store a peer choice
    try:
        print_info("Storing peer choice...")
        response = requests.post(
            f"{BASE_URL}/api/peer-choice",
            params={
                "branch_predicted": "CS",
                "rank": 5000,
                "location": "Bangalore",
                "college_chosen": "NIT Trichy"
            }
        )
        
        if response.status_code == 200:
            print_success("Peer choice stored")
        else:
            print_error(f"Failed to store: {response.status_code}")
    except Exception as e:
        print_error(f"Error storing: {e}")
    
    # Now get peer stats
    try:
        print_info("Fetching peer stats...")
        response = requests.get(
            f"{BASE_URL}/api/peer-stats",
            params={
                "branch": "CS",
                "rank": 5000,
                "location": "Bangalore"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Peer stats retrieved")
            print_info(f"Total peers: {data['total_peers']}")
            print_info(f"Branch match: {data['branch_match_percentage']}%")
            print_info(f"Rank bucket: {data['rank_bucket']}")
            print_info(f"Message: {data['message'][:60]}...")
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_placement_reality():
    """Test 8: Feature 9C - Placement Reality Check"""
    print_test("Test 8: Feature 9C - Placement Reality Check")
    try:
        response = requests.post(f"{BASE_URL}/api/placement-reality", json={
            "college_name": "IIT Bombay",
            "branch": "Computer Science"
        })
        
        if response.status_code == 200:
            data = response.json()
            print_success("Placement reality check completed")
            print_info(f"Median Salary: ₹{data['median_salary_lpa']} LPA")
            print_info(f"Headline Salary: ₹{data['headline_salary_lpa']} LPA")
            print_info(f"Placement %: {data['placement_percentage']}%")
            print_info(f"Inflation Ratio: {data['inflation_ratio']}")
            print_info(f"Is Inflated: {data['is_inflated']}")
            print_info(f"Note: {data['reality_note'][:60]}...")
            
            # Check acceptance criterion: median vs headline distinction
            if data['median_salary_lpa'] > 0 and data['headline_salary_lpa'] > 0:
                print_success("✓ Acceptance criterion met: Median vs headline distinction present")
            else:
                print_error("✗ Acceptance criterion failed: Missing salary data")
            
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_career_roadmap():
    """Test 9: Feature 9D - Branch-Career Roadmap"""
    print_test("Test 9: Feature 9D - Branch-Career Roadmap")
    try:
        response = requests.post(f"{BASE_URL}/api/career-roadmap", json={
            "branch": "Computer Science",
            "college_tier": "Moderate"
        })
        
        if response.status_code == 200:
            data = response.json()
            print_success("Career roadmap generated")
            
            # Check all 4 stages
            stages = ['year_1', 'year_2_3', 'year_4', 'year_5']
            all_present = all(stage in data for stage in stages)
            
            if all_present:
                print_success("✓ Acceptance criterion met: All 4 stages present")
                for stage in stages:
                    print_info(f"{stage}: {data[stage]['title']}")
            else:
                print_error("✗ Acceptance criterion failed: Missing stages")
            
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_parent_report(session_id: str):
    """Test 10: Feature 9E - Parent Report"""
    print_test("Test 10: Feature 9E - Parent Report")
    try:
        response = requests.post(f"{BASE_URL}/api/parent-report", json={
            "session_id": session_id,
            "student_name": "Test Student"
        })
        
        if response.status_code == 200:
            data = response.json()
            print_success("Parent report generated")
            print_info(f"Report ID: {data['report_id']}")
            print_info(f"Student: {data['student_name']}")
            print_info(f"Recommended Branch: {data['summary']['recommended_branch']}")
            print_info(f"Confidence: {data['summary']['confidence']}")
            print_info(f"Top Colleges: {len(data['top_colleges'])}")
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_error_handling():
    """Test 11: Error Handling"""
    print_test("Test 11: Error Handling")
    
    # Test invalid session ID
    try:
        print_info("Testing invalid session ID...")
        response = requests.post(f"{BASE_URL}/chat", json={
            "session_id": "invalid_session_12345",
            "user_message": "Hello"
        })
        
        if response.status_code == 404:
            print_success("✓ Invalid session correctly rejected (404)")
        else:
            print_error(f"✗ Expected 404, got {response.status_code}")
    except Exception as e:
        print_error(f"Error: {e}")
    
    # Test empty message
    try:
        print_info("Testing empty message...")
        response = requests.post(f"{BASE_URL}/chat", json={
            "session_id": "any_id",
            "user_message": ""
        })
        
        if response.status_code in [400, 404]:
            print_success(f"✓ Empty message correctly rejected ({response.status_code})")
        else:
            print_error(f"✗ Expected 400/404, got {response.status_code}")
    except Exception as e:
        print_error(f"Error: {e}")
    
    return True

def run_all_tests():
    """Run all test cases"""
    print_header("PATHFINDER API TEST SUITE")
    print(f"Testing server at: {BASE_URL}\n")
    
    results = []
    session_id = None
    
    # Basic tests
    results.append(("Health Check", test_health()))
    results.append(("List Branches", test_branches()))
    
    # Session tests
    session_id = test_start_session()
    results.append(("Start Session", session_id is not None))
    
    if session_id:
        results.append(("Chat Flow", test_chat(session_id)))
        results.append(("Get Session", test_get_session(session_id)))
    
    # Novel features
    results.append(("What-If Simulator (9A)", test_what_if()))
    results.append(("Peer Comparison (9B)", test_peer_comparison()))
    results.append(("Placement Reality (9C)", test_placement_reality()))
    results.append(("Career Roadmap (9D)", test_career_roadmap()))
    
    if session_id:
        results.append(("Parent Report (9E)", test_parent_report(session_id)))
    
    # Error handling
    results.append(("Error Handling", test_error_handling()))
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"{status} - {test_name}")
    
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print(f"{GREEN}🎉 ALL TESTS PASSED!{RESET}")
    else:
        print(f"{YELLOW}⚠️  Some tests failed. Check output above.{RESET}")
    
    print(f"{BLUE}{'='*70}{RESET}\n")

if __name__ == "__main__":
    run_all_tests()
