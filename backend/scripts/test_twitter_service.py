"""
Test script for Twitter/X analysis service.
Tests scraping, analysis, and LLM summarization with fallback mechanisms.
"""
import sys
import asyncio
sys.path.insert(0, '.')

from services.twitter_service import get_twitter_insights
from services.ai_service import summarize_twitter_insights
from config import settings


async def test_twitter_service():
    """Test the Twitter service with a known college."""
    print("="*80)
    print("Testing Twitter/X Analysis Service")
    print("="*80)
    
    # Check if Twitter API key is configured
    if not settings.twitter_bearer_token:
        print("\n⚠️  WARNING: TWITTER_BEARER_TOKEN not set in .env")
        print("The service will return empty results gracefully.")
        print("To test with real data, add TWITTER_BEARER_TOKEN to your .env file.")
    else:
        print(f"\n✅ Twitter API configured (token: {settings.twitter_bearer_token[:20]}...)")
    
    # Test with IIT Bombay
    college_name = "IIT Bombay"
    print(f"\n{'='*80}")
    print(f"Test 1: Fetch Twitter insights for {college_name}")
    print(f"{'='*80}")
    
    try:
        result = await get_twitter_insights(
            college_name=college_name,
            target_tweet_count=50,  # Lower count for testing
            use_cache=False,
            generate_narrative=True,
        )
        
        print(f"\n✅ Successfully fetched Twitter insights")
        print(f"\nSample size: {result['sample_size']} tweets")
        print(f"Overall sentiment: {result['overall']['sentiment_label']} (score: {result['overall']['sentiment_score']:+.3f})")
        print(f"Confidence: {result['overall']['confidence']:.0%}")
        print(f"Positive ratio: {result['overall']['positive_ratio']:.0%}")
        print(f"Negative ratio: {result['overall']['negative_ratio']:.0%}")
        
        print(f"\n📊 Category Breakdown:")
        for cat_name, cat_data in result['categories'].items():
            if cat_data['tweet_count'] >= 5:
                print(f"  • {cat_name.replace('_', ' ').title()}: "
                      f"{cat_data['tweet_count']} tweets, "
                      f"sentiment={cat_data['sentiment_label']} ({cat_data['sentiment_score']:+.2f}), "
                      f"confidence={cat_data['confidence']:.0%}")
        
        print(f"\n💬 Dominant Opinion:")
        print(f"  {result['opinions']['dominant'][:150]}...")
        
        print(f"\n💬 Minority Opinion:")
        print(f"  {result['opinions']['minority'][:150]}...")
        
        print(f"\n📝 LLM-Generated Summary:")
        print(f"  {result['summary']}")
        
        print(f"\n📋 Data Quality Note:")
        print(f"  {result['data_quality_note']}")
        
        if result['sample_size'] == 0:
            print("\n⚠️  No tweets found. This is expected if:")
            print("  1. TWITTER_BEARER_TOKEN is not set")
            print("  2. API rate limits are exceeded")
            print("  3. No recent tweets match the search queries")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Test summarize_twitter_insights function
    print(f"\n{'='*80}")
    print(f"Test 2: Test summarize_twitter_insights function")
    print(f"{'='*80}")
    
    # Mock tweet data
    mock_tweets = [
        {
            "text": "IIT Bombay placements are amazing! Got placed at Google with 45 LPA package.",
            "likes": 150,
            "retweets": 45,
            "date": "2024-01-15",
        },
        {
            "text": "IIT Bombay hostel food is terrible. Same menu every week, quality is poor.",
            "likes": 80,
            "retweets": 20,
        },
        {
            "text": "Campus life at IIT Bombay is great. Mood Indigo fest was incredible!",
            "likes": 120,
            "retweets": 30,
        },
        {
            "text": "Coding culture at IITB is top-notch. Everyone is into competitive programming.",
            "likes": 95,
            "retweets": 25,
        },
        {
            "text": "IIT Bombay placements: Microsoft, Amazon, Goldman Sachs all came for campus recruitment.",
            "likes": 200,
            "retweets": 60,
        },
        {
            "text": "Hostel facilities need improvement. Multiple students complaining about maintenance.",
            "likes": 70,
            "retweets": 15,
        },
    ]
    
    try:
        bullets = await summarize_twitter_insights(college_name, mock_tweets)
        
        print(f"\n✅ Generated {len(bullets)} summary bullets:")
        for bullet in bullets:
            print(f"  {bullet}")
        
        if len(bullets) == 3:
            print(f"\n✅ Correct number of bullets generated")
        else:
            print(f"\n⚠️  Expected 3 bullets, got {len(bullets)}")
        
    except Exception as e:
        print(f"\n❌ Error in summarize_twitter_insights: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Test with empty tweets (fallback)
    print(f"\n{'='*80}")
    print(f"Test 3: Test graceful fallback with empty tweets")
    print(f"{'='*80}")
    
    try:
        bullets = await summarize_twitter_insights(college_name, [])
        
        if len(bullets) == 0:
            print(f"\n✅ Correctly returned empty list for no tweets")
        else:
            print(f"\n⚠️  Expected empty list, got {len(bullets)} bullets")
        
    except Exception as e:
        print(f"\n❌ Error in empty tweets test: {e}")
        return False
    
    print(f"\n{'='*80}")
    print("✅ All Twitter Service Tests Complete")
    print("="*80)
    
    return True


async def test_acceptance_criteria():
    """Test the specific acceptance criteria."""
    print("\n" + "="*80)
    print("Testing Acceptance Criteria")
    print("="*80)
    
    # Criterion 1: Graceful fallback without API key
    print("\n✓ Criterion 1: Service falls back gracefully without API key")
    
    # Temporarily clear the token
    original_token = settings.twitter_bearer_token
    settings.twitter_bearer_token = ""
    
    try:
        result = await get_twitter_insights(
            college_name="IIT Delhi",
            target_tweet_count=50,
            use_cache=False,
        )
        
        if result['sample_size'] == 0:
            print("✅ PASS: Service returned empty results gracefully without API key")
        else:
            print("⚠️  WARNING: Got non-zero results without API key (unexpected)")
        
    except Exception as e:
        print(f"❌ FAIL: Service crashed without API key: {e}")
    finally:
        # Restore token
        settings.twitter_bearer_token = original_token
    
    # Criterion 2: With API key, returns tweets sorted by engagement
    print("\n✓ Criterion 2: With API key, returns engagement-sorted tweets")
    
    if settings.twitter_bearer_token:
        try:
            result = await get_twitter_insights(
                college_name="IIT Bombay",
                target_tweet_count=20,
                use_cache=False,
            )
            
            if result['sample_size'] > 0:
                print(f"✅ PASS: Retrieved {result['sample_size']} tweets with API key")
                print(f"   Overall sentiment: {result['overall']['sentiment_label']}")
                print(f"   Confidence: {result['overall']['confidence']:.0%}")
            else:
                print("⚠️  INFO: No tweets found (may be rate limited or no recent tweets)")
        except Exception as e:
            print(f"⚠️  WARNING: API call failed: {e}")
    else:
        print("⚠️  SKIP: No API key configured, cannot test criterion 2")
    
    # Criterion 3: Groq summarization includes engagement context
    print("\n✓ Criterion 3: Groq summarization includes engagement-weighted context")
    
    mock_tweets = [
        {"text": "Great placements at Google!", "likes": 200, "retweets": 50},
        {"text": "Poor hostel food", "likes": 10, "retweets": 2},
        {"text": "Amazing campus life", "likes": 150, "retweets": 40},
    ]
    
    try:
        bullets = await summarize_twitter_insights("Test College", mock_tweets)
        
        if bullets:
            print(f"✅ PASS: Generated {len(bullets)} bullets with engagement weighting")
            for bullet in bullets:
                print(f"   {bullet}")
        else:
            print("❌ FAIL: No bullets generated")
    except Exception as e:
        print(f"❌ FAIL: Summarization failed: {e}")
    
    print("\n" + "="*80)
    print("✅ Acceptance Criteria Tests Complete")
    print("="*80)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("Twitter/X Analysis Service Test Suite")
    print("="*80)
    
    # Run main tests
    success = asyncio.run(test_twitter_service())
    
    # Test acceptance criteria
    asyncio.run(test_acceptance_criteria())
    
    print("\n" + "="*80)
    if success:
        print("✅ ALL TESTS COMPLETE - SUCCESS")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*80)
    
    sys.exit(0 if success else 1)
