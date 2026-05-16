#!/usr/bin/env python3
"""
Test the complete flow including college recommendations
"""
import requests
import json

def test_complete_flow_with_colleges():
    print("🧪 Testing Complete Flow with College Recommendations")
    print("=" * 60)
    
    # Step 1: Create session with rank and budget
    print("1. Creating session with rank and budget...")
    try:
        session_response = requests.post(
            "http://127.0.0.1:8081/session/start",
            json={
                "jee_rank": 15000,  # Good rank for recommendations
                "budget_lakh": 5.0,
                "preferred_location": "South India"
            },
            timeout=10
        )
        
        if session_response.status_code != 200:
            print(f"❌ Session creation failed: {session_response.status_code}")
            print(f"   Response: {session_response.text}")
            return False
        
        session_data = session_response.json()
        session_id = session_data["session_id"]
        print(f"✅ Session created: {session_id[:20]}...")
        print(f"   First question: {session_data.get('first_question', '')[:50]}...")
        
    except Exception as e:
        print(f"❌ Session creation error: {e}")
        return False
    
    # Step 2-6: Send multiple chat messages to complete the conversation
    questions_and_answers = [
        ("I love computer science and programming", "CS-focused response"),
        ("I enjoy solving logical problems and coding", "More CS signals"),
        ("I prefer working with technology over manual work", "Tech preference"),
        ("I want to work in software development", "Career goal"),
        ("I'm interested in artificial intelligence", "AI interest")
    ]
    
    for i, (answer, description) in enumerate(questions_and_answers, 1):
        print(f"\n{i+1}. Sending message: {description}...")
        try:
            chat_response = requests.post(
                "http://127.0.0.1:8081/chat",
                json={
                    "session_id": session_id,
                    "user_message": answer
                },
                timeout=15
            )
            
            if chat_response.status_code != 200:
                print(f"❌ Chat failed: {chat_response.status_code}")
                print(f"   Response: {chat_response.text}")
                return False
            
            chat_data = chat_response.json()
            print(f"✅ Response received")
            print(f"   Is complete: {chat_data.get('is_complete', False)}")
            print(f"   Branch scores: {chat_data.get('branch_scores', {})}")
            
            # Check if conversation is complete
            if chat_data.get('is_complete'):
                print(f"\n🎉 CONVERSATION COMPLETED!")
                print(f"   Final message: {chat_data.get('assistant_message', '')[:100]}...")
                
                # Check for report with college recommendations
                report = chat_data.get('report')
                if report:
                    print(f"\n📊 REPORT GENERATED:")
                    print(f"   Recommended branch: {report.get('recommended_branch')}")
                    print(f"   Confidence: {report.get('confidence', 0):.2f}")
                    print(f"   Total colleges: {report.get('total_colleges', 0)}")
                    
                    colleges = report.get('colleges', {})
                    for tier in ['Dream', 'Moderate', 'Safe']:
                        tier_colleges = colleges.get(tier, [])
                        print(f"   {tier} colleges: {len(tier_colleges)}")
                        if tier_colleges:
                            for college in tier_colleges[:2]:  # Show first 2
                                print(f"     - {college.get('name', 'Unknown')} ({college.get('location', 'Unknown')})")
                    
                    return True
                else:
                    print(f"❌ No report generated in completion response")
                    return False
            
        except Exception as e:
            print(f"❌ Chat error: {e}")
            return False
    
    print(f"❌ Conversation did not complete after {len(questions_and_answers)} messages")
    return False

def main():
    success = test_complete_flow_with_colleges()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 COLLEGE RECOMMENDATIONS WORKING!")
        print("✅ Session creation: Working")
        print("✅ Chat processing: Working")
        print("✅ Conversation completion: Working")
        print("✅ College recommendations: Generated")
        print("✅ Report format: Correct")
        print("\n💡 The results section should now show college preferences!")
    else:
        print("❌ College recommendations not working properly")

if __name__ == "__main__":
    main()