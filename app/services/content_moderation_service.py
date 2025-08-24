# app/services/content_moderation_service.py

class ContentModerationService:
    """
    A service for moderating text content to identify inappropriate or fraudulent patterns.
    For a production environment, this would integrate with a robust AI moderation API
    (e.g., Google Cloud Natural Language API, Azure Content Moderator, OpenAI's moderation API).
    """

    def __init__(self):
        # Initialize any necessary clients or load models here if using local AI
        pass

    def analyze_text(self, text: str) -> dict:
        """
        Analyzes the given text for inappropriate content, fraud indicators, or spam.
        Returns a dictionary with moderation results.
        """
        text_lower = text.lower()
        
        inappropriate_keywords = [
            "sex", "porn", "nude", "erotic", "adult content", "hate speech",
            "violence", "gore", "weapon", "drug", "illegal", "scam", "fraud",
            "fake money", "counterfeit", "spam", "clickbait", "phishing"
        ]
        
        fraud_keywords = [
            "guaranteed profit", "get rich quick", "no risk", "investment opportunity",
            "pyramid scheme", "too good to be true", "urgent money", "wire transfer only"
        ]

        inappropriate_found = False
        fraud_found = False
        reasons = []

        for keyword in inappropriate_keywords:
            if keyword in text_lower:
                inappropriate_found = True
                reasons.append(f"Contains inappropriate keyword: '{keyword}'")
        
        for keyword in fraud_keywords:
            if keyword in text_lower:
                fraud_found = True
                reasons.append(f"Contains potential fraud keyword: '{keyword}'")

        # Simple check for excessive capitalization (often used in spam/scams)
        if len(text) > 20 and sum(1 for c in text if c.isupper()) / len(text) > 0.5:
            reasons.append("Excessive capitalization detected")

        # Simple check for unusual character repetition (e.g., "!!!!", "#####")
        import re
        if re.search(r'(.){3,}', text_lower): # Detects 4 or more repetitions of any character
            reasons.append("Unusual character repetition detected")

        return {
            "inappropriate": inappropriate_found,
            "fraudulent": fraud_found,
            "flagged": inappropriate_found or fraud_found or bool(reasons), # Flag if any rule is triggered
            "reasons": reasons if reasons else ["No issues detected"]
        }