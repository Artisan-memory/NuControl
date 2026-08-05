import json

import aiohttp


async def fetch_currency() -> tuple[float, float]:
    """Return current USD and EUR rates (RUB) from the Central Bank of Russia feed."""
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            text = await response.text()

    json_data = json.loads(text[text.find('{'):text.rfind('}') + 1])
    usd_rate = round(json_data['Valute']['USD']['Value'], 2)
    eur_rate = round(json_data['Valute']['EUR']['Value'], 2)

    return usd_rate, eur_rate
