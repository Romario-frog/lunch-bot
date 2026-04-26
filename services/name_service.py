from __future__ import annotations

import re

_LAT_TO_UK = {
    'shch': 'щ', 'sch': 'щ', 'zh': 'ж', 'ch': 'ч', 'sh': 'ш', 'kh': 'х', 'ts': 'ц', 'yu': 'ю', 'ya': 'я', 'ye': 'є', 'yi': 'ї',
    'a': 'а', 'b': 'б', 'v': 'в', 'h': 'г', 'g': 'г', 'd': 'д', 'e': 'е', 'z': 'з', 'y': 'и', 'i': 'і', 'j': 'й',
    'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н', 'o': 'о', 'p': 'п', 'r': 'р', 's': 'с', 't': 'т', 'u': 'у', 'f': 'ф',
    'c': 'к', 'w': 'в', 'q': 'к', 'x': 'кс'
}
_CYR_TO_LAT = {
    'щ': 'shch', 'ж': 'zh', 'ч': 'ch', 'ш': 'sh', 'х': 'kh', 'ц': 'ts', 'ю': 'yu', 'я': 'ya', 'є': 'ye', 'ї': 'yi',
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'ґ': 'g', 'д': 'd', 'е': 'e', 'з': 'z', 'и': 'y', 'і': 'i', 'й': 'i',
    'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f',
    'ь': '', '’': '', "'": ''
}


def compact_name(value: str) -> str:
    return re.sub(r'[^0-9a-zа-яіїєґ]+', '', str(value).casefold())


def latin_to_ukrainian(value: str) -> str:
    text = str(value).casefold()
    result = []
    i = 0
    keys = sorted(_LAT_TO_UK, key=len, reverse=True)
    while i < len(text):
        matched = False
        for key in keys:
            if text.startswith(key, i):
                result.append(_LAT_TO_UK[key])
                i += len(key)
                matched = True
                break
        if not matched:
            result.append(text[i])
            i += 1
    return ''.join(result)


def ukrainian_to_latin(value: str) -> str:
    return ''.join(_CYR_TO_LAT.get(ch, ch) for ch in str(value).casefold())


def name_variants(value: str) -> set[str]:
    text = str(value).strip()
    parts = [p for p in re.split(r'\s+', text) if p]
    variants = {compact_name(text), compact_name(latin_to_ukrainian(text)), compact_name(ukrainian_to_latin(text))}
    if len(parts) >= 2:
        swapped = ' '.join([parts[1], parts[0], *parts[2:]])
        variants |= {compact_name(swapped), compact_name(latin_to_ukrainian(swapped)), compact_name(ukrainian_to_latin(swapped))}
    return {v for v in variants if v}
