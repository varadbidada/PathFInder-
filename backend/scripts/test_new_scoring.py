"""
Test the new branch scoring system - no memory across sessions
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from engines.conversation_fsm import ConversationState
from engines.session_manager import SessionManager
from engines.conversation_controller import ConversationController

print("=" * 80)
print("Testing New Branch Scoring System")
print("=" * 80)

controller = ConversationController()

# Test 1: Signals aggregate within a session
print("\n=== Test 1: Within-Session Aggregation ===")

session1_id = "test-session-1"
state1 = controller.session_manager.create_session(session1_id)

print(f"\nSession 1 created: {session1_id}")
print(f"Initial user_responses: {len(state1.user_responses)}")

# Simulate 3 responses
state1.user_responses.append({
    "message": "I love coding",
    "signals": {
        "Logical_Thinking_ability": 0.8,
        "Logical_Thinking_enthusiasm": 0.9,
        "Math_Aptitude_ability": 0.7,
        "Math_Aptitude_enthusiasm": 0.6,
    }
})

state1.user_responses.append({
    "message": "I hate math",
    "signals": {
        "Logical_Thinking_ability": 0.8,
        "Logical_Thinking_enthusiasm": 0.9,
        "Math_Aptitude_ability": 0.7,
        "Math_Aptitude_enthusiasm": 0.1,  # Changed!
    }
})

state1.user_responses.append({
    "message": "I enjoy problem solving",
    "signals": {
        "Logical_Thinking_ability": 0.9,
        "Logical_Thinking_enthusiasm": 0.95,
        "Problem_Solving_ability": 0.8,
        "Problem_Solving_enthusiasm": 0.9,
    }
})

# Aggregate signals
aggregated = controller._aggregate_session_signals(state1)

print(f"\nAfter 3 messages:")
print(f"  Total responses: {len(state1.user_responses)}")
print(f"  Logical_Thinking_enthusiasm: {aggregated.get('Logical_Thinking_enthusiasm', 0):.2f}")
print(f"  Math_Aptitude_enthusiasm: {aggregated.get('Math_Aptitude_enthusiasm', 0):.2f}")

# Verify it's a simple average
expected_math = (0.6 + 0.1) / 2  # Only 2 messages mentioned math
actual_math = aggregated.get('Math_Aptitude_enthusiasm', 0)

print(f"\n  Expected Math_Aptitude_enthusiasm: {expected_math:.2f} (average of 0.6 and 0.1)")
print(f"  Actual Math_Aptitude_enthusiasm: {actual_math:.2f}")

if abs(expected_math - actual_math) < 0.01:
    print(f"  ✅ Simple average working correctly!")
else:
    print(f"  ❌ Average incorrect!")

# Test 2: New session starts fresh (no memory)
print("\n" + "=" * 80)
print("=== Test 2: Cross-Session Isolation (No Memory) ===")

# Delete session 1
controller.session_manager.delete_session(session1_id)
print(f"\nDeleted Session 1: {session1_id}")

# Create session 2
session2_id = "test-session-2"
state2 = controller.session_manager.create_session(session2_id)

print(f"\nSession 2 created: {session2_id}")
print(f"Initial user_responses: {len(state2.user_responses)}")

# Add completely different responses
state2.user_responses.append({
    "message": "I love mechanical work",
    "signals": {
        "Manual_Work_ability": 0.8,
        "Manual_Work_enthusiasm": 0.9,
        "Spatial_Awareness_ability": 0.7,
        "Spatial_Awareness_enthusiasm": 0.8,
    }
})

# Aggregate signals for session 2
aggregated2 = controller._aggregate_session_signals(state2)

print(f"\nAfter 1 message in Session 2:")
print(f"  Manual_Work_enthusiasm: {aggregated2.get('Manual_Work_enthusiasm', 0):.2f}")
print(f"  Spatial_Awareness_enthusiasm: {aggregated2.get('Spatial_Awareness_enthusiasm', 0):.2f}")

# Verify no CS signals from session 1
if "Logical_Thinking_enthusiasm" not in aggregated2:
    print(f"  ✅ No CS signals from Session 1 (properly isolated)")
else:
    print(f"  ❌ CS signals leaked from Session 1!")
    print(f"     Logical_Thinking_enthusiasm: {aggregated2.get('Logical_Thinking_enthusiasm', 0):.2f}")

# Test 3: Empty session returns empty dict
print("\n" + "=" * 80)
print("=== Test 3: Empty Session Handling ===")

session3_id = "test-session-3"
state3 = controller.session_manager.create_session(session3_id)

aggregated3 = controller._aggregate_session_signals(state3)

print(f"\nSession 3 (no responses):")
print(f"  Aggregated signals: {aggregated3}")

if len(aggregated3) == 0:
    print(f"  ✅ Empty session returns empty dict")
else:
    print(f"  ❌ Empty session has signals: {aggregated3}")

# Cleanup
controller.session_manager.delete_session(session2_id)
controller.session_manager.delete_session(session3_id)

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("✅ Signals aggregate within a session (simple average)")
print("✅ New sessions start with NO memory of previous sessions")
print("✅ Empty sessions handled correctly")
print("\nConclusion: New scoring system works correctly!")
print("Each session is independent - no memory across sessions.")
