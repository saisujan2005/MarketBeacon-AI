ALERT_THRESHOLD = 85


def should_alert(score):

    return score >= ALERT_THRESHOLD