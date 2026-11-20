ALLOWED_YEAR_LEVELS = ("1st Year", "2nd Year", "3rd Year", "4th Year")
# Example programs for docs/templates only — import accepts any non-empty program.
EXAMPLE_PROGRAMS = ("BSBA", "BSIT", "BSCS", "BSIS")

YEAR_LEVEL_LOOKUP = {value.casefold(): value for value in ALLOWED_YEAR_LEVELS}

MAX_PROGRAM_LENGTH = 50


def normalize_program(value: str) -> str | None:
    cleaned = " ".join(value.strip().split())
    if not cleaned:
        return None
    if len(cleaned) > MAX_PROGRAM_LENGTH:
        return None
    return cleaned.upper()


def normalize_year_level(value: str) -> str | None:
    return YEAR_LEVEL_LOOKUP.get(value.strip().casefold())


def normalize_location(value: str) -> str:
    cleaned = " ".join(value.strip().split())
    if not cleaned:
        return ""
    return cleaned.title()
