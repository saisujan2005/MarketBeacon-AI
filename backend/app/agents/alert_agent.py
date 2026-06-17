# Minimum importance score to trigger an alert
# 90 = only MONETARY_POLICY (95), GEOPOLITICAL (92), MARKET_FLOW (90)
# This keeps alerts meaningful — roughly top 15% of articles
ALERT_THRESHOLD = 90


def should_alert(score):
    if score is None:
        return False
    return score >= ALERT_THRESHOLD