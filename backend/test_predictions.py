import json

with open('data/cutoff_predictions_2025.json') as f:
    preds = json.load(f)

print(f"Total predictions: {len(preds)}")
print("\nSearching for IIT Bombay Computer Science:")
for p in preds:
    if 'bombay' in p['institute'].lower() and 'computer' in p['branch'].lower():
        print(f"Found: {p['institute']} - {p['branch']}")
        print(f"Predicted 2025: {p['predicted_closing_rank_2025']}")
        print(f"Actual 2024: {p['actual_closing_rank_2024']}")
        break
else:
    print("Not found - showing all IIT Bombay branches:")
    for p in preds:
        if 'bombay' in p['institute'].lower():
            print(f"  {p['branch']}")

