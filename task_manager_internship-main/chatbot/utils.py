import re

try:
    from deep_translator import GoogleTranslator
except ImportError:  # pragma: no cover - optional dependency
    GoogleTranslator = None

try:
    from langdetect import LangDetectException, detect
except ImportError:  # pragma: no cover - optional dependency
    LangDetectException = Exception
    detect = None


HINDI_CHAR_PATTERN = re.compile(r"[\u0900-\u097F]")
HINGLISH_KEYWORDS = {
    "mera",
    "meri",
    "mere",
    "mujhe",
    "task",
    "tasks",
    "pending",
    "completed",
    "high",
    "priority",
    "aaj",
    "kal",
    "kitna",
    "kitne",
    "hours",
    "time",
    "kaam",
    "dikhao",
    "batao",
    "show",
}


def _contains_hindi_script(text: str) -> bool:
    return bool(HINDI_CHAR_PATTERN.search(text or ""))


def _looks_like_hinglish(text: str) -> bool:
    words = {word.lower() for word in re.findall(r"[A-Za-z]+", text or "")}
    return bool(words & HINGLISH_KEYWORDS)


def detect_language(text: str) -> str:
    """
    Return 'hi' for Hindi/Hinglish input and 'en' for English.
    """
    cleaned_text = (text or "").strip()
    if not cleaned_text:
        return "en"

    if _contains_hindi_script(cleaned_text):
        return "hi"

    if _looks_like_hinglish(cleaned_text):
        return "hi"

    if detect:
        try:
            language = detect(cleaned_text)
            if language == "hi":
                return "hi"
        except LangDetectException:
            pass

    return "en"


def _translate_text(text: str, source_language: str, target_language: str) -> str:
    if not text or source_language == target_language:
        return text

    if GoogleTranslator is None:
        return text

    try:
        translator = GoogleTranslator(source=source_language, target=target_language)
        return translator.translate(text)
    except Exception:
        return text


def translate_to_english(text: str) -> str:
    return _translate_text(text, source_language="auto", target_language="en")


def translate_to_hindi(text: str) -> str:
    return _translate_text(text, source_language="auto", target_language="hi")
