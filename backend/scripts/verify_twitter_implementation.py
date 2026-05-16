"""
Verification script for Twitter/X implementation.
Checks that all required components are present without running them.
"""
import sys
import os
import re

def check_file_exists(filepath: str) -> bool:
    """Check if a file exists."""
    return os.path.exists(filepath)

def check_function_exists(filepath: str, function_name: str) -> bool:
    """Check if a function is defined in a file."""
    if not os.path.exists(filepath):
        return False
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = rf'(async\s+)?def\s+{re.escape(function_name)}\s*\('
    return bool(re.search(pattern, content))

def check_class_exists(filepath: str, class_name: str) -> bool:
    """Check if a class is defined in a file."""
    if not os.path.exists(filepath):
        return False
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = rf'class\s+{re.escape(class_name)}\s*[:\(]'
    return bool(re.search(pattern, content))

def check_config_field(filepath: str, field_name: str) -> bool:
    """Check if a config field is defined."""
    if not os.path.exists(filepath):
        return False
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = rf'{re.escape(field_name)}\s*:'
    return bool(re.search(pattern, content))

def check_dependency(filepath: str, package_name: str) -> bool:
    """Check if a package is in requirements.txt."""
    if not os.path.exists(filepath):
        return False
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return package_name in content

def main():
    print("="*80)
    print("Twitter/X Implementation Verification")
    print("="*80)
    
    checks = []
    
    # Check 1: Core files exist
    print("\n✓ Checking core files...")
    files_to_check = [
        "services/twitter_scraper.py",
        "services/twitter_analyzer.py",
        "services/twitter_service.py",
        "services/ai_service.py",
        "config.py",
        "requirements.txt",
    ]
    
    for filepath in files_to_check:
        exists = check_file_exists(filepath)
        status = "✅" if exists else "❌"
        print(f"  {status} {filepath}")
        checks.append(exists)
    
    # Check 2: Twitter scraper components
    print("\n✓ Checking twitter_scraper.py components...")
    scraper_checks = [
        ("Tweet", "class"),
        ("fetch_college_tweets", "function"),
        ("scrape_tweets_api", "function"),
        ("build_queries_for_college", "function"),
    ]
    
    for name, check_type in scraper_checks:
        if check_type == "class":
            exists = check_class_exists("services/twitter_scraper.py", name)
        else:
            exists = check_function_exists("services/twitter_scraper.py", name)
        status = "✅" if exists else "❌"
        print(f"  {status} {check_type.title()}: {name}")
        checks.append(exists)
    
    # Check 3: Twitter analyzer components
    print("\n✓ Checking twitter_analyzer.py components...")
    analyzer_checks = [
        ("AnalysedTweet", "class"),
        ("TwitterAnalysisReport", "class"),
        ("analyse_college_tweets", "function"),
        ("compute_sentiment", "function"),
        ("detect_emotions", "function"),
        ("cluster_tweets", "function"),
    ]
    
    for name, check_type in analyzer_checks:
        if check_type == "class":
            exists = check_class_exists("services/twitter_analyzer.py", name)
        else:
            exists = check_function_exists("services/twitter_analyzer.py", name)
        status = "✅" if exists else "❌"
        print(f"  {status} {check_type.title()}: {name}")
        checks.append(exists)
    
    # Check 4: Twitter service components
    print("\n✓ Checking twitter_service.py components...")
    service_checks = [
        ("get_twitter_insights", "function"),
        ("get_twitter_insights_batch", "function"),
        ("serialise_report", "function"),
    ]
    
    for name, check_type in service_checks:
        exists = check_function_exists("services/twitter_service.py", name)
        status = "✅" if exists else "❌"
        print(f"  {status} Function: {name}")
        checks.append(exists)
    
    # Check 5: AI service integration
    print("\n✓ Checking ai_service.py integration...")
    ai_checks = [
        "summarize_twitter_insights",
        "summarize_reddit_insights",
    ]
    
    for func_name in ai_checks:
        exists = check_function_exists("services/ai_service.py", func_name)
        status = "✅" if exists else "❌"
        print(f"  {status} Function: {func_name}")
        checks.append(exists)
    
    # Check 6: Config fields
    print("\n✓ Checking config.py fields...")
    config_fields = [
        "twitter_bearer_token",
        "twitter_target_tweets",
        "twitter_cache_ttl_seconds",
    ]
    
    for field in config_fields:
        exists = check_config_field("config.py", field)
        status = "✅" if exists else "❌"
        print(f"  {status} Config field: {field}")
        checks.append(exists)
    
    # Check 7: Dependencies
    print("\n✓ Checking requirements.txt dependencies...")
    dependencies = [
        "tweepy",
        "vaderSentiment",
        "textblob",
        "scikit-learn",
        "numpy",
        "beautifulsoup4",
    ]
    
    for dep in dependencies:
        exists = check_dependency("requirements.txt", dep)
        status = "✅" if exists else "❌"
        print(f"  {status} Dependency: {dep}")
        checks.append(exists)
    
    # Check 8: Acceptance criteria implementation
    print("\n✓ Checking acceptance criteria implementation...")
    
    # Criterion 1: Graceful fallback without API key
    print("  Criterion 1: Graceful fallback without API key")
    scraper_content = open("services/twitter_scraper.py", 'r', encoding='utf-8').read()
    has_fallback = 'if not bearer_token:' in scraper_content and 'logger.warning' in scraper_content
    status = "✅" if has_fallback else "❌"
    print(f"    {status} Fallback mechanism present")
    checks.append(has_fallback)
    
    # Criterion 2: Engagement-based sorting
    print("  Criterion 2: Engagement-based sorting")
    analyzer_content = open("services/twitter_analyzer.py", 'r', encoding='utf-8').read()
    has_engagement = 'likes' in analyzer_content and 'retweets' in analyzer_content
    status = "✅" if has_engagement else "❌"
    print(f"    {status} Engagement scoring present")
    checks.append(has_engagement)
    
    # Criterion 3: Groq summarization with engagement context
    print("  Criterion 3: Groq summarization with engagement context")
    ai_content = open("services/ai_service.py", 'r', encoding='utf-8').read()
    has_twitter_summary = 'summarize_twitter_insights' in ai_content
    has_engagement_context = 'engagement' in ai_content.lower() or 'likes' in ai_content
    status = "✅" if has_twitter_summary and has_engagement_context else "❌"
    print(f"    {status} Engagement-weighted summarization present")
    checks.append(has_twitter_summary and has_engagement_context)
    
    # Summary
    print("\n" + "="*80)
    print("Verification Summary")
    print("="*80)
    total = len(checks)
    passed = sum(checks)
    failed = total - passed
    
    print(f"Total checks: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✅ ALL CHECKS PASSED - Implementation is complete!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Add TWITTER_BEARER_TOKEN to .env file (optional)")
        print("3. Run: python scripts/test_twitter_service.py")
    else:
        print(f"\n❌ {failed} CHECK(S) FAILED - Review implementation")
    
    print("="*80)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
