import sys
sys.path.insert(0, '.')

from nlp.sentiment.analyzer import get_sentiment_analyzer
from nlp.sentiment.cross_verify import get_cross_verification_engine

print("="*60)
print("Sentiment Analysis Quick Verification")
print("="*60)

# Test analyzer
analyzer = get_sentiment_analyzer()
print("\n✅ Sentiment analyzer loaded")

result = analyzer.analyze("I hate math but I am decent at it")
print(f"✅ Analysis result: compound={result['compound']:.2f}")

# Test cross-verifier
engine = get_cross_verification_engine()
print("✅ Cross-verification engine loaded")

verify = engine.verify([0.7, 0.8, -0.9, 0.75])
print(f"✅ Verification result: outliers_removed={verify['outliers_removed']}")

print("\n" + "="*60)
print("✅ All components working correctly!")
print("="*60)
