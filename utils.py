KEYWORD_MAP = {
    "Food": ["pizza", "burger", "restaurant", "swiggy", "zomato", "coffee", "grocery", "tea", "lunch", "dinner", "biryani"],
    "Travel": ["uber", "ola", "bus", "train", "flight", "petrol", "fuel", "taxi", "auto", "metro"],
    "Shopping": ["amazon", "flipkart", "shirt", "shoes", "dress", "mall"],
    "Bills": ["electricity", "wifi", "recharge", "rent", "water", "gas", "internet"],
    "Entertainment": ["movie", "netflix", "spotify", "game", "concert"],
    "Health": ["medicine", "doctor", "hospital", "pharmacy", "clinic"],
}

CATEGORIES = list(KEYWORD_MAP.keys()) + ["Others"]


def predict_category(description):
    text = (description or "").lower()
    for category, words in KEYWORD_MAP.items():
        for w in words:
            if w in text:
                return category
    return "Others"
