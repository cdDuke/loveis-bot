from .budget_service import currency_symbol


def flower_budget_guidance(currency: str | None, budget: str) -> str:
    symbol = currency_symbol(currency)
    text = budget.lower()

    if any(marker in text for marker in ("мал", "до", "1000", "1500", "2000", "2500")):
        return (
            f"Бюджет выглядит небольшим. Лучше предложить минималистичный букет: "
            f"1–3 акцентных цветка, зелень, аккуратная упаковка, примерный чек в {symbol}."
        )
    if any(marker in text for marker in ("больш", "7000", "10000", "20000", "прем")):
        return (
            f"Бюджет позволяет сделать более премиальный букет: больше фактуры, "
            f"плотная упаковка, открытка, примерный чек в {symbol}."
        )
    return f"Дай сбалансированный вариант букета и обязательно укажи, что цена в {symbol} примерная."

