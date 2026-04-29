import re
from bs4 import BeautifulSoup, NavigableString
from config.settings import MAX_QUOTE_CHARS, MIN_QUOTE_CHARS
from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException

def normalize(text: str) -> str:
    """
    Normaliza un string para comparación:
    minúsculas, sin acentos, sin puntuación.
    """
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ü": "u", "ñ": "n", "ç": "c", "à": "a", "è": "e",
        "ì": "i", "ò": "o", "ù": "u", "â": "a", "ê": "e",
        "î": "i", "ô": "o", "û": "u", "ä": "a", "ë": "e",
        "ï": "i", "ö": "o",
    }
    text = text.lower()
    for accented, plain in replacements.items():
        text = text.replace(accented, plain)
    # Remover todo lo que no sea letra o espacio
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text.strip()

def author_matches(result_author: str, expected_author: str) -> bool:
    """
    Valida que el autor del resultado sea el autor que buscamos.
    Usa el apellido como mínimo para evitar falsos negativos
    por variaciones de nombre (Pablo Neruda vs Neruda, Pablo).
    """
    norm_result   = normalize(result_author)
    norm_expected = normalize(expected_author)
 
    # Coincidencia exacta
    if norm_result == norm_expected:
        return True
 
    # Verificar que al menos el apellido (última palabra) coincida
    expected_parts = norm_expected.split()
    for part in expected_parts:
        if len(part) > 3 and part in norm_result:  # ignorar palabras muy cortas
            return True
 
    return False

def find_best_match_url(book_links, author_links, author):

    max_results = 10
    match_path = None

    for i, (book_link, author_link) in enumerate(zip(book_links, author_links)):
        result_title  = book_link.get_text(strip=True)
        result_author = author_link.get_text(strip=True)
        result_path   = book_link.get("href", "")
 
        if author_matches(result_author, author):
            match_path = result_path
            break
 
        if i >= max_results - 1:
            break

    return match_path

def remove_base(url, base):
    return url.removeprefix(base)

def clean_quote(div):
    text_nodes = [
        node.strip()
        for node in div.children
        if isinstance(node, NavigableString)   
        and node.strip()                
    ]
 
    quote_text = " ".join(text_nodes)
 
    quote_text = (
        quote_text
        .replace("\u201c", "")  
        .replace("\u201d", "")   
        .replace('"',     "")
        .replace("―",     "")
        .replace("\u2015","")   
        .strip()
    )
 
    if MIN_QUOTE_CHARS < len(quote_text) <= MAX_QUOTE_CHARS:
        return quote_text
 
    return None

def get_top_5_quotes(soup, limit):
    raw_quotes = []
    quote_divs = soup.select(".quoteText")

    if not quote_divs:
        return []
    
    for div in quote_divs:

        cleaned = clean_quote(div)
        if cleaned:
            raw_quotes.append(cleaned)
 
        if len(raw_quotes) >= limit:   # tomar el doble, luego filtramos
            break

    return raw_quotes

def translate_to_english(quote):

    detected_lang = detect(quote)
    if detected_lang == "en":
        return quote
    
    translated = GoogleTranslator(source="auto", target="en").translate(quote)
    return translated.strip()
