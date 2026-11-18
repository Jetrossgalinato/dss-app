ALLOWED_PROGRAMS = ("BSBA", "BSIT", "BSCS", "BSIS")
ALLOWED_YEAR_LEVELS = ("1st Year", "2nd Year", "3rd Year", "4th Year")

PROGRAM_LOOKUP = {value.casefold(): value for value in ALLOWED_PROGRAMS}
YEAR_LEVEL_LOOKUP = {value.casefold(): value for value in ALLOWED_YEAR_LEVELS}


def normalize_program(value: str) -> str | None:
    return PROGRAM_LOOKUP.get(value.strip().casefold())


def normalize_year_level(value: str) -> str | None:
    return YEAR_LEVEL_LOOKUP.get(value.strip().casefold())


def normalize_location(value: str) -> str:
    cleaned = " ".join(value.strip().split())
    if not cleaned:
        return ""
    return cleaned.title()
