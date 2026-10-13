from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from bot.config import TravelSite
from bot.services.budget_service import currency_symbol, travel_defaults


@dataclass(frozen=True)
class TravelInput:
    destination_type: str
    destination: str
    transport: str
    currency: str
    fuel_consumption: float | None = None
    fuel_price: float | None = None
    days: int = 3
    nights: int = 2


class TravelProvider(ABC):
    @abstractmethod
    async def search_tickets(self, trip: TravelInput) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def estimate_trip(self, trip: TravelInput) -> dict[str, Any]:
        raise NotImplementedError


class MockTravelProvider(TravelProvider):
    """Mock provider with replaceable methods for future ticket APIs."""

    def __init__(self, travel_sites: tuple[TravelSite, ...]) -> None:
        self.travel_sites = travel_sites

    async def search_tickets(self, trip: TravelInput) -> dict[str, Any]:
        defaults = travel_defaults(trip.currency)
        if trip.transport == "Машина":
            distance = _estimate_distance(trip.destination_type, trip.destination, trip.transport)
            consumption = trip.fuel_consumption or 8
            fuel_price = trip.fuel_price or defaults["fuel_price"]
            liters = distance * 2 * consumption / 100
            road_cost = round(liters * fuel_price)
            return {
                "min": road_cost,
                "max": road_cost,
                "distance_km": distance,
                "road_cost": road_cost,
                "note": "Расчет для машины сделан по примерному расстоянию туда-обратно.",
            }

        min_price, max_price = defaults["tickets"].get(trip.transport, defaults["tickets"]["Самолет"])
        if trip.destination_type == "Страна":
            min_price = round(min_price * 1.6)
            max_price = round(max_price * 1.9)

        return {
            "min": min_price,
            "max": max_price,
            "distance_km": _estimate_distance(trip.destination_type, trip.destination, trip.transport),
            "road_cost": None,
            "note": "Это примерный диапазон, без проверки живых тарифов.",
        }

    async def estimate_trip(self, trip: TravelInput) -> dict[str, Any]:
        defaults = travel_defaults(trip.currency)
        tickets = await self.search_tickets(trip)
        symbol = currency_symbol(trip.currency)

        housing = defaults["housing_per_night"] * trip.nights
        food = defaults["food_per_day"] * trip.days
        local_transport = defaults["local_transport"]
        entertainment = defaults["entertainment"]
        reserve = defaults["reserve"]

        total_min = tickets["min"] + housing + food + local_transport + entertainment + reserve
        total_max = tickets["max"] + housing + food + local_transport + entertainment + reserve

        return {
            "destination_type": trip.destination_type,
            "destination": trip.destination,
            "transport": trip.transport,
            "currency": trip.currency,
            "symbol": symbol,
            "days": trip.days,
            "nights": trip.nights,
            "route": f"Ваш город → {trip.destination} → ваш город",
            "distance_km": tickets["distance_km"],
            "time_in_way": _estimate_time(trip.transport, tickets["distance_km"]),
            "tickets_min": tickets["min"],
            "tickets_max": tickets["max"],
            "housing": housing,
            "food": food,
            "local_transport": local_transport,
            "entertainment": entertainment,
            "reserve": reserve,
            "total_min": total_min,
            "total_max": total_max,
            "ticket_note": tickets["note"],
            "sites": self.travel_sites,
        }


def format_trip_estimate(estimate: dict[str, Any]) -> str:
    symbol = estimate["symbol"]
    links = "\n".join(f"• {site.name}: {site.url}" for site in estimate["sites"])

    return (
        "✈️ Примерный план путешествия\n\n"
        f"Маршрут: {estimate['route']}\n"
        f"Транспорт: {estimate['transport']}\n"
        f"Время в пути: примерно {estimate['time_in_way']}\n"
        f"Расстояние: примерно {estimate['distance_km']} км\n\n"
        "Билеты / дорога:\n"
        f"• примерно {estimate['tickets_min']:,}–{estimate['tickets_max']:,} {symbol}\n"
        f"• {estimate['ticket_note']}\n\n"
        "Общий чек на пару:\n"
        f"• дорога: {estimate['tickets_min']:,}–{estimate['tickets_max']:,} {symbol}\n"
        f"• жилье ({estimate['nights']} ночи): примерно {estimate['housing']:,} {symbol}\n"
        f"• еда ({estimate['days']} дня): примерно {estimate['food']:,} {symbol}\n"
        f"• такси/местный транспорт: примерно {estimate['local_transport']:,} {symbol}\n"
        f"• развлечения: примерно {estimate['entertainment']:,} {symbol}\n"
        f"• запасной бюджет: примерно {estimate['reserve']:,} {symbol}\n\n"
        f"Итого: примерно {estimate['total_min']:,}–{estimate['total_max']:,} {symbol}\n\n"
        "Где проверить актуальные цены:\n"
        f"{links}\n\n"
        "Важно: это предварительная оценка без реального API билетов. Перед покупкой проверь цены по ссылкам."
    ).replace(",", " ")


def _estimate_distance(destination_type: str, destination: str, transport: str) -> int:
    base = 650 if destination_type == "Город" else 2400
    destination_factor = min(max(len(destination), 4), 18) / 10
    transport_factor = 0.8 if transport == "Самолет" else 1.0
    return round(base * destination_factor * transport_factor)


def _estimate_time(transport: str, distance_km: int) -> str:
    if transport == "Самолет":
        hours = max(1.5, distance_km / 700 + 2)
    elif transport == "Поезд":
        hours = max(3, distance_km / 70)
    elif transport == "Автобус":
        hours = max(2, distance_km / 55)
    else:
        hours = max(1, distance_km / 75)

    if hours < 24:
        return f"{round(hours, 1)} ч"
    days = hours / 24
    return f"{round(days, 1)} дня"

