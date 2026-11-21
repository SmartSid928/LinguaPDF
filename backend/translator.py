import time
import html
import requests


# Supported languages
LANGUAGES = {
    "en": "English",
    "ta": "Tamil",
    "hi": "Hindi",
    "ml": "Malayalam",
    "te": "Telugu",
    "bn": "Bengali",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh-CN": "Chinese (Simplified)",
    "ar": "Arabic",
    "ru": "Russian",
    "pt": "Portuguese",
    "ur": "Urdu",
    "id": "Indonesian",
    "tr": "Turkish",
    "vi": "Vietnamese",
    "th": "Thai",
    "fa": "Persian",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "pa": "Punjabi",
    "sw": "Swahili",
    "nl": "Dutch",
    "pl": "Polish",
    "he": "Hebrew"
}


# Return supported languages for frontend
def get_languages():
    return [
        {"code": code, "name": name}
        for code, name in LANGUAGES.items()
    ]


# Split text into UTF-8 safe chunks
def split_text(text, max_bytes=450):

    chunks = []
    current_chunk = ""

    for word in text.split(" "):

        candidate = (
            current_chunk + " " + word
            if current_chunk else word
        )

        if len(candidate.encode("utf-8")) > max_bytes:

            if current_chunk:
                chunks.append(current_chunk)

            current_chunk = word

        else:
            current_chunk = candidate

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


# Translate text using MyMemory API
def translate_text(text, source_code, target_code):

    if not text or not text.strip():
        return ""

    if source_code == target_code:
        return text

    if source_code == "auto":
        source_code = "en"

    if source_code not in LANGUAGES:
        raise ValueError("Unsupported source language.")

    if target_code not in LANGUAGES:
        raise ValueError("Unsupported target language.")

    chunks = split_text(text)

    translated_chunks = []

    session = requests.Session()

    for index, chunk in enumerate(chunks):

        response = None

        # Retry temporary rate limits and server errors
        for attempt in range(3):

            try:
                response = session.get(
                    "https://api.mymemory.translated.net/get",
                    params={
                        "q": chunk,
                        "langpair": f"{source_code}|{target_code}"
                    },
                    timeout=30
                )

                if response.status_code == 429:
                    if attempt < 2:
                        time.sleep(5 * (attempt + 1))
                        continue

                    raise RuntimeError(
                        "MyMemory rate limit reached. "
                        "Please wait a few minutes before trying again."
                    )

                response.raise_for_status()
                break

            except requests.exceptions.Timeout:
                if attempt < 2:
                    time.sleep(2)
                    continue

                raise RuntimeError(
                    "Translation request timed out. Please try again."
                )

            except requests.exceptions.HTTPError:
                raise RuntimeError(
                    f"Translation API returned HTTP "
                    f"{response.status_code}."
                )

            except requests.exceptions.RequestException as error:
                if attempt < 2:
                    time.sleep(2)
                    continue

                raise RuntimeError(
                    f"Could not connect to translation service: {error}"
                )

        if response is None:
            raise RuntimeError("Translation service did not respond.")

        try:
            data = response.json()
        except ValueError:
            raise RuntimeError(
                "Translation service returned an invalid response."
            )

        if data.get("responseStatus") != 200:
            raise RuntimeError(
                data.get(
                    "responseDetails",
                    "Translation service failed."
                )
            )

        translated = data.get("responseData", {}).get(
            "translatedText"
        )

        if translated is None:
            raise RuntimeError(
                "Translation service returned empty data."
            )

        translated_chunks.append(
            html.unescape(translated)
        )

        # Small pause between requests to reduce request bursts
        if index < len(chunks) - 1:
            time.sleep(1)

    session.close()

    return " ".join(translated_chunks)
