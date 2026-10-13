import logging

from openai import AsyncOpenAI


logger = logging.getLogger(__name__)

LOVEIS_SYSTEM_STYLE = (
    "Ты LoveIS — теплый любовный помощник. Отвечай как живой человек с опытом отношений: "
    "спокойно, нежно, без осуждения. Помогай пользователю сделать отношения теплее. "
    "Не манипулируй, не дави, не советуй ревность, контроль, угрозы или токсичное поведение. "
    "Пиши по-русски, красиво, но естественно."
)


class AIService:
    def __init__(self, api_key: str | None, model: str) -> None:
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None

    @property
    def enabled(self) -> bool:
        return self.client is not None

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.85,
        max_tokens: int = 1200,
    ) -> str:
        if not self.client:
            return (
                "Сейчас генерация через OpenAI не подключена.\n\n"
                "Добавь OPENAI_API_KEY в .env, перезапусти бота — и я сразу смогу генерировать "
                "живые ответы, идеи, стихи, букеты и сценарии."
            )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception:
            logger.exception("OpenAI request failed")
            return (
                "Не получилось обратиться к AI-сервису. Проверь OPENAI_API_KEY, модель и интернет, "
                "а потом попробуй еще раз."
            )

        content = response.choices[0].message.content if response.choices else None
        return (content or "Не получилось сгенерировать ответ. Попробуй еще раз.").strip()

    async def generate_image_prompt(self, details: str) -> str:
        return await self.generate_text(
            LOVEIS_SYSTEM_STYLE,
            build_image_prompt(details),
            temperature=0.8,
            max_tokens=700,
        )

    async def generate_image(self, image_prompt: str) -> str | None:
        # Hook for OpenAI Images API or another image provider. The bot works without image generation.
        logger.info("Image generation hook called with prompt length=%s", len(image_prompt))
        return None


def build_sweet_reply_prompt(message_text: str, style: str) -> str:
    return f"""
Раздел: "Ответить мило".
Пользователь прислал сообщение от партнера:
{message_text}

Стиль ответа: {style}.

Сгенерируй 3 варианта ответа. Требования:
1. Живо, естественно, без роботских и слишком пафосных фраз.
2. Не дави и не манипулируй.
3. В конце коротко объясни, какой вариант лучше выбрать и почему.
Оформи аккуратно, с короткими заголовками.
""".strip()


def build_videos_prompt(target: str) -> str:
    return f"""
Раздел: "Любовные видео".
Сделай идеи любовных видео: {target}.

Нужно 5 идей:
• короткое видео для сторис
• видео-поздравление
• видео с текстом на фоне музыки
• видео с воспоминаниями
• видео-сюрприз

Для каждой идеи дай: название, сценарий, какие кадры нужны, пример текста,
какую музыку выбрать по настроению, детальный промт для картинки/фона.
Не предлагай скачивать видео из интернета.
""".strip()


def build_couple_photos_prompt(choice: str, description: str) -> str:
    return f"""
Раздел: "Парные фото".
Выбор пользователя: {choice}.
Описание пары или пожелания: {description or "нет описания"}.

Дай идеи парных фото: поза, концепция, одежда, фон, настроение, свет,
вариант для аватарки, вариант дома, вариант на улице, Pinterest-style кадр.
Добавь детальный промт для генерации изображения. Если описание пары есть — адаптируй под него.
""".strip()


def build_date_prompt(budget: str, date_format: str, currency_symbol: str) -> str:
    return f"""
Раздел: "Свидание".
Бюджет: {budget}.
Валюта: {currency_symbol}.
Формат: {date_format}.

Составь план свидания под бюджет:
• название идеи
• что делать по шагам
• примерный чек
• что входит в чек
• что можно заменить дешевле
• что подготовить заранее
• как красиво пригласить

Если бюджет "нету денег / своими руками", предложи теплые DIY-идеи: письмо,
пикник дома, прогулка, фильм, самодельный квест, рисунок, коробка воспоминаний.
Все цены пиши примерно.
""".strip()


def build_travel_romance_prompt(base_estimate: str) -> str:
    return f"""
Раздел: "Путешествие".
Ниже уже есть расчет от mock-провайдера:
{base_estimate}

Добавь короткий романтичный план на 3 дня: как сделать поездку теплой для пары,
что подготовить заранее, как красиво предложить поездку. Не меняй цифры и подчеркни,
что цены примерные и актуальность нужно проверить по ссылкам.
""".strip()


def build_compliments_prompt(target: str, style: str) -> str:
    return f"""
Раздел: "Комплименты".
Кому: {target}.
Стиль: {style}.

Сгенерируй 10 живых, нежных и небанальных комплиментов.
Не делай их пошлыми, токсичными или чрезмерно пафосными.
""".strip()


def build_situation_prompt(description: str, goal: str, safety_note: str | None = None) -> str:
    return f"""
Раздел: "Анализ ситуации".
Описание ситуации:
{description}

Чего хочет пользователь: {goal}.
Предупреждение безопасности: {safety_note or "опасных признаков не найдено"}.

Ответь тепло и спокойно:
• что, скорее всего, происходит
• что лучше не делать
• что можно сделать
• какой текст можно отправить
• почему этот вариант лучше

Не поощряй манипуляции, давление, ревность, контроль или угрозы.
Если есть риск насилия или угрозы жизни, на первое место поставь безопасность.
""".strip()


def build_wish_prompt(description: str) -> str:
    return f"""
Раздел: "Желание".
Условия пользователя:
{description}

Придумай 7 желаний, которые приятны обоим:
• милое
• романтичное
• смешное
• полезное для отношений
• интимно-нежное, но без пошлости
• творческое
• необычное

Для каждого объясни, почему оно хорошо для обоих.
Не предлагай опасные, унизительные, токсичные или незаконные желания.
""".strip()


def build_diy_prompt(details: str, currency_symbol: str, *, trend: bool = False) -> str:
    trend_text = "Сделай одну современную трендовую идею в стиле соцсетей." if trend else ""
    return f"""
Раздел: "Милые идеи своими руками".
Условия: {details or "пользователь не дал условий"}.
Валюта: {currency_symbol}.
{trend_text}

Предложи идеи подарков/сюрпризов своими руками. Учитывай бюджет, время, для кого и повод,
если это указано. Для каждой идеи дай:
• материалы
• шаги
• примерный чек
• сколько времени займет
• как красиво подарить
• промт для генерации картинки идеи
""".strip()


def build_flowers_prompt(
    recipient: str,
    loved_flowers: str,
    colors: str,
    reason: str,
    budget: str,
    currency_symbol: str,
    guidance: str,
) -> str:
    return f"""
Раздел: "Цветы".
Для кого: {recipient}.
Любимые цветы: {loved_flowers}.
Любимые цвета: {colors}.
Повод: {reason}.
Бюджет: {budget} {currency_symbol}.
Ориентир: {guidance}.

Сгенерируй букет:
• название букета
• список цветов
• количество каждого цветка
• упаковка
• цветовая гамма
• примерная цена
• что написать в открытке
• как вручить
• промт для генерации картинки букета

Если бюджет маленький — предложи красивый минималистичный букет.
Если большой — более премиальный. Обязательно напиши, что цена примерная.
""".strip()


def build_poems_prompt(description: str) -> str:
    return f"""
Раздел: "Стихи".
Описание пользователя:
{description}

Сгенерируй 2 варианта стиха:
1. Нежный и простой.
2. Более романтичный.

Стихи должны быть естественными, не слишком старомодными, без тяжеловесной лексики.
""".strip()


def build_image_prompt(details: str) -> str:
    return f"""
Сделай детальный промт для генерации изображения по теме любви/отношений.
Детали: {details}.

Промт должен включать: сцену, свет, стиль, настроение, одежду/объекты, фон,
цветовую палитру, композицию, уровень реалистичности. Пиши по-русски.
""".strip()

