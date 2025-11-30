# telegram-be/src/utils/priority_detector.py - FULL FILE
import re
from typing import List, Optional

class PriorityDetector:
    """
    Detect ticket priority based on message keywords
    Future: Will integrate with Gemini AI for better accuracy
    """
    
    KEYWORDS = {
        "urgent": [
            # Indonesian
            "urgent", "segera", "emergency", "darurat", "asap", "sekarang juga",
            "cepat banget", "sangat penting", "kritis", "mati", "down", "rusak total",
            "tidak bisa", "error fatal", "gawat", "parah banget", "tolong cepat",
            # English
            "critical", "immediately", "right now", "broken", "crashed", "fatal error",
            # Slang
            "parah", "buset", "anjir error", "aduh gawat", "woi cepet"
        ],
        "high": [
            # Indonesian
            "penting", "butuh cepat", "masalah besar", "error", "gagal", 
            "tidak berfungsi", "bug", "issue", "problem serius", "harap segera",
            "mohon diprioritaskan", "kenapa tidak bisa", "rusak", "bermasalah",
            # English
            "important", "need fast", "big problem", "failed", "not working",
            "serious problem",
            # Slang
            "gimana nih", "kok error", "kenapa sih"
        ],
        "medium": [
            # Indonesian
            "tolong", "bantuan", "help", "bingung", "gimana", "bagaimana", 
            "kenapa", "kok", "mohon bantu", "minta tolong",
            # English
            "help", "please", "how to", "can you", "need help",
            # Slang
            "bro tolong", "gan bantuin", "min"
        ],
        "low": [
            # Indonesian
            "info", "informasi", "mau tanya", "tanya", "kapan", "berapa",  # ✅ PINDAHIN "tanya" ke sini
            "ada ga", "bisa ga", "boleh tanya", "sekedar tanya", "pertanyaan",
            # English
            "info", "information", "just asking", "question", "when", "how much",
            "is there", "can i ask",
            # Slang
            "btw", "fyi", "mau nanya", "pengen tau"
        ]
    }

    # Negation words to reduce priority
    NEGATION_WORDS = [
        "tidak urgent", "bukan urgent", "gak urgent", "ga urgent",
        "not urgent", "no urgent", "santai", "slow", "nanti"
    ]
    
    @classmethod
    def detect_priority(cls, text: str, use_ai: bool = False) -> str:
        """
        Detect priority from text content
        
        Args:
            text: Message text to analyze
            use_ai: Use AI detection (Gemini) - NOT IMPLEMENTED YET
        
        Returns:
            Priority level: urgent, high, medium, or low
        """
        if not text:
            return "medium"
        
        # Future: Use Gemini AI if enabled
        if use_ai:
            return cls._detect_with_ai(text)
        
        # Current: Use keyword-based detection
        return cls._detect_with_keywords(text)
    
    @classmethod
    def _detect_with_keywords(cls, text: str) -> str:
        """Keyword-based detection (current implementation)"""
        if not text:
            return "medium"
        
        text_normalized = text.lower().strip()
        print(f"🔍 Detecting priority for: '{text_normalized}'")  # ✅ DEBUG
        
        # Check for negation first
        for negation in cls.NEGATION_WORDS:
            if negation in text_normalized:
                print(f"❌ Negation found: {negation}")  # ✅ DEBUG
                return "medium"
        
        # Check urgent first (highest priority)
        for keyword in cls.KEYWORDS["urgent"]:
            if keyword.lower() in text_normalized:
                print(f"🔴 URGENT keyword found: {keyword}")  # ✅ DEBUG
                return "urgent"
        
        # Check high
        for keyword in cls.KEYWORDS["high"]:
            if keyword.lower() in text_normalized:
                print(f"🟠 HIGH keyword found: {keyword}")  # ✅ DEBUG
                return "high"
        
        # Check medium (if not commented)
        for keyword in cls.KEYWORDS["medium"]:
            if keyword.lower() in text_normalized:
                print(f"🟡 MEDIUM keyword found: {keyword}")  # ✅ DEBUG
                return "medium"
        
        # Check low
        for keyword in cls.KEYWORDS["low"]:
            if keyword.lower() in text_normalized:
                print(f"🟢 LOW keyword found: {keyword}")  # ✅ DEBUG
                return "low"
        
        print(f"⚪ No keyword match, defaulting to medium")  # ✅ DEBUG
        return "medium"
    
    @classmethod
    def _detect_with_ai(cls, text: str) -> str:
        """
        AI-based detection using Gemini API
        
        TODO: Implement Gemini integration
        
        Future implementation:
        1. Call Gemini API with prompt
        2. Parse priority from response
        3. Fallback to keywords if API fails
        
        Example implementation:
```python
        import google.generativeai as genai
        
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f'''
        Analyze this customer message and classify the urgency level.
        Return ONLY one word: urgent, high, medium, or low
        
        Message: {text}
        
        Classification:
        '''
        
        try:
            response = model.generate_content(prompt)
            priority = response.text.strip().lower()
            
            # Validate response
            if priority in ["urgent", "high", "medium", "low"]:
                return priority
            else:
                # Fallback to keywords if AI returns invalid
                return cls._detect_with_keywords(text)
        except Exception as e:
            # Fallback to keywords if AI fails
            logger.warning(f"AI detection failed, using keywords: {e}")
            return cls._detect_with_keywords(text)
```
        """
        # For now, fallback to keywords
        # TODO: Remove this after Gemini integration
        return cls._detect_with_keywords(text)
    
    @classmethod
    def detect_from_messages(cls, messages: List[str], limit: int = 3, use_ai: bool = False) -> str:
        """
        Detect priority from multiple messages
        Takes highest priority found in recent messages
        
        Args:
            messages: List of message texts
            limit: Number of recent messages to analyze
            use_ai: Use AI detection (Gemini) - NOT IMPLEMENTED YET
        """
        priorities = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
        max_priority = "low"
        max_score = 1
        
        for msg in messages[:limit]:
            detected = cls.detect_priority(msg, use_ai=use_ai)
            score = priorities.get(detected, 2)
            if score > max_score:
                max_score = score
                max_priority = detected
        
        return max_priority


# ============================================
# FUTURE: Gemini AI Integration
# ============================================

class GeminiPriorityDetector:
    """
    Gemini AI-based priority detection
    
    TODO: Implement after Gemini API key is configured
    
    Setup required:
    1. pip install google-generativeai
    2. Set GEMINI_API_KEY in environment
    3. Enable detect_priority(use_ai=True)
    
    Benefits:
    - Better context understanding
    - Multilingual support (Indo + English + Slang)
    - Handles sarcasm and negation
    - No keyword maintenance needed
    
    Trade-offs:
    - Latency: ~500ms vs 1ms (keywords)
    - Cost: ~$0.0001 per request
    - Requires internet connection
    """
    
    @staticmethod
    def detect(text: str) -> str:
        """
        TODO: Implement Gemini detection
        
        Example code (for future reference):
        
        import google.generativeai as genai
        import os
        
        # Configure Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-pro')
        
        # Prompt engineering
        prompt = f'''
        You are a customer support priority classifier.
        
        Analyze this customer message and classify urgency into EXACTLY one of these levels:
        - urgent: Emergency, critical issue, system down, blocking work
        - high: Important issue, needs quick response, functionality broken
        - medium: General help request, questions, minor issues
        - low: Information request, general inquiry, no blocking issues
        
        Consider:
        1. Keywords (urgent, help, error, broken, etc)
        2. Tone (calm vs panicked)
        3. Context (questioning vs demanding)
        4. Negations ("not urgent" should be low priority)
        
        Message: "{text}"
        
        Respond with ONLY ONE WORD (urgent/high/medium/low):
        '''
        
        try:
            response = model.generate_content(prompt)
            priority = response.text.strip().lower()
            
            if priority in ["urgent", "high", "medium", "low"]:
                return priority
            else:
                return "medium"  # Safe default
                
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return "medium"  # Fallback
        """
        raise NotImplementedError("Gemini integration pending")