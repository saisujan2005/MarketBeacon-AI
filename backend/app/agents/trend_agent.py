from collections import Counter


def detect_trends(posts):

    event_types = [
        post.event_type
        for post in posts
    ]

    counts = Counter(
        event_types
    )

    return counts