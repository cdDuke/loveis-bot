CURRENCIES = {
    "KZT": {"symbol": "₸", "name": "Тенге", "country": "Казахстан"},
    "RUB": {"symbol": "₽", "name": "Рубли", "country": "Россия"},
}

DATE_BUDGET_LABELS = {
    "free": "нету денег / своими руками",
    "up_2500": "до 2500",
    "2500_4000": "2500–4000",
    "4000_7000": "4000–7000",
    "7000_plus": "7000+",
}

TRAVEL_DEFAULTS = {
    "RUB": {
        "housing_per_night": 3500,
        "food_per_day": 1800,
        "local_transport": 1500,
        "entertainment": 3000,
        "reserve": 3000,
        "fuel_price": 65,
        "tickets": {
            "Самолет": (8000, 26000),
            "Поезд": (3000, 12000),
            "Автобус": (1500, 7000),
        },
    },
    "KZT": {
        "housing_per_night": 18000,
        "food_per_day": 7000,
        "local_transport": 5000,
        "entertainment": 12000,
        "reserve": 15000,
        "fuel_price": 290,
        "tickets": {
            "Самолет": (25000, 95000),
            "Поезд": (8000, 35000),
            "Автобус": (5000, 25000),
        },
    },
}


def currency_symbol(currency: str | None) -> str:
    return CURRENCIES.get(currency or "RUB", CURRENCIES["RUB"])["symbol"]


def currency_name(currency: str | None) -> str:
    return CURRENCIES.get(currency or "RUB", CURRENCIES["RUB"])["name"]


def format_date_budget(code: str, currency: str, custom_budget: str | None = None) -> str:
    symbol = currency_symbol(currency)
    if code == "custom" and custom_budget:
        return f"{custom_budget} {symbol}"
    label = DATE_BUDGET_LABELS.get(code, code)
    if code == "free":
        return label
    return f"{label} {symbol}"


def travel_defaults(currency: str | None) -> dict:
    return TRAVEL_DEFAULTS.get(currency or "RUB", TRAVEL_DEFAULTS["RUB"])


def default_fuel_price(currency: str | None) -> int:
    return int(travel_defaults(currency)["fuel_price"])

