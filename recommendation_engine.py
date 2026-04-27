import json
import numpy as np

# Mapping company index to symbols (Mock list representing our 13 targets)
COMPANIES = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", 
    "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "ADA-USD", "XRP-USD"
]

def generate_recommendation_report(raw_scores, top_k=3, threshold=0.5):
    """
    Translates raw neural network output into actionable buy/sell signals.
    """
    if len(raw_scores) != len(COMPANIES):
        raise ValueError(f"Score array length {len(raw_scores)} does not match defined companies {len(COMPANIES)}.")
        
    recommendations = []
    
    for i, score in enumerate(raw_scores):
        asset = COMPANIES[i]
        # Example Risk Filter / Buy Signal policy
        signal = "STRONG BUY" if score >= threshold else ("BUY" if score > 0 else "HOLD/SELL")
        recommendations.append({
            "asset": asset,
            "forecast_score": float(score),
            "signal": signal
        })
        
    # Sort by highest score
    recommendations = sorted(recommendations, key=lambda x: x["forecast_score"], reverse=True)
    
    report = {
        "summary": f"Top {top_k} recommendations based on Dual Transformer Analytics",
        "top_picks": recommendations[:top_k],
        "all_assets": recommendations
    }
    
    return report

def save_report(report, filepath="recommendation_report.json"):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
    print(f"Report saved to {filepath}")

def get_formatted_text(report):
    lines = ["\n📊 [Dual Transformer] Today's Recommendations 📊", "="*45]
    for pick in report["top_picks"]:
        lines.append(f"[{pick['signal']}] {pick['asset']} (AI Score: {pick['forecast_score']:.4f})")
    lines.append("="*45)
    return "\n".join(lines)

if __name__ == "__main__":
    from inference_harness import run_inference
    scores = run_inference()
    
    # Process Recommendation
    report = generate_recommendation_report(scores)
    save_report(report)
    
    # Print to console
    print(get_formatted_text(report))
