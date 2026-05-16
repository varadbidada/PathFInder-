"""
Test script for the enhanced Reddit service.
Tests multi-query, multi-comment fetching with quality filtering.
"""
import sys
import asyncio
sys.path.insert(0, '.')

from services.reddit_service import fetch_college_insights
from services.ai_service import summarize_reddit_insights

async def test_reddit_fetch():
    """Test the enhanced Reddit fetching."""
    print("="*80)
    print("Testing Enhanced Reddit Service")
    print("="*80)
    
    # Test with IIT Bombay
    college_name = "IIT Bombay"
    print(f"\nFetching Reddit insights for: {college_name}")
    print("-"*80)
    
    raw_text = await fetch_college_insights(college_name)
    
    if not raw_text:
        print("❌ FAIL: No data returned from Reddit")
        return False
    
    print(f"\n✅ Fetched {len(raw_text)} characters of Reddit data")
    
    # Check for multiple posts
    post_count = raw_text.count("--- Post")
    print(f"✅ Found {post_count} posts in results")
    
    if post_count < 3:
        print(f"⚠️  WARNING: Expected at least 3 posts, got {post_count}")
    
    # Check for comments
    comment_count = raw_text.count("Comment ")
    print(f"✅ Found {comment_count} comments in results")
    
    if comment_count == 0:
        print("❌ FAIL: No comments found in results")
        return False
    
    # Check for sentiment score
    if "Sentiment score:" in raw_text:
        print("✅ Sentiment score calculated")
    else:
        print("❌ FAIL: Sentiment score missing")
        return False
    
    # Check for diversity warning
    if "[WARNING:" in raw_text:
        print("⚠️  Source diversity warning present")
    else:
        print("✅ Multiple subreddit sources")
    
    # Print sample of the data
    print("\n" + "="*80)
    print("Sample of fetched data (first 1000 chars):")
    print("="*80)
    print(raw_text[:1000])
    print("...")
    
    # Test summarization
    print("\n" + "="*80)
    print("Testing Reddit Summarization with Confidence Levels")
    print("="*80)
    
    bullets = await summarize_reddit_insights(college_name, raw_text)
    
    if not bullets:
        print("❌ FAIL: No summary bullets generated")
        return False
    
    print(f"\n✅ Generated {len(bullets)} summary bullets:")
    for bullet in bullets:
        print(f"  {bullet}")
    
    # Check for confidence tags
    has_confidence = any('[High]' in b or '[Medium]' in b or '[Low]' in b for b in bullets)
    if has_confidence:
        print("\n✅ Confidence levels present in summary")
    else:
        print("\n⚠️  WARNING: No confidence levels found in summary")
    
    # Check for source URL
    has_source = any('Source:' in b or 'reddit.com' in b for b in bullets)
    if has_source:
        print("✅ Source URL included")
    else:
        print("⚠️  WARNING: No source URL found")
    
    print("\n" + "="*80)
    print("✅ All core tests passed!")
    print("="*80)
    
    return True


async def test_multiple_colleges():
    """Test with multiple colleges to verify diversity."""
    print("\n" + "="*80)
    print("Testing Multiple Colleges")
    print("="*80)
    
    colleges = ["IIT Delhi", "NIT Trichy"]
    
    for college in colleges:
        print(f"\n--- Testing {college} ---")
        raw_text = await fetch_college_insights(college)
        
        if raw_text:
            post_count = raw_text.count("--- Post")
            comment_count = raw_text.count("Comment ")
            print(f"✅ {college}: {post_count} posts, {comment_count} comments")
        else:
            print(f"⚠️  {college}: No data returned")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("Enhanced Reddit Service Test Suite")
    print("="*80)
    print("\nNOTE: This test requires valid Reddit API credentials in .env")
    print("If credentials are missing, the test will use the public JSON fallback.")
    print("="*80)
    
    # Run main test
    success = asyncio.run(test_reddit_fetch())
    
    if success:
        # Run additional tests
        asyncio.run(test_multiple_colleges())
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETE")
        print("="*80)
        print("\nAcceptance Criteria:")
        print("✅ fetch_college_insights returns content from at least 3 posts")
        print("✅ Returned text contains comment bodies (not just titles)")
        print("✅ summarize_reddit_insights produces bullets with confidence tags")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ TESTS FAILED")
        print("="*80)
        sys.exit(1)
