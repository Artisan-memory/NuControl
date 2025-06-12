import json

import aiohttp


async def fetch_currency():
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            text = await response.text()

            json_data = json.loads(text[text.find('{'):text.rfind('}') + 1])
            usd_rate = round(json_data['Valute']['USD']['Value'], 2)
            eur_rate = round(json_data['Valute']['EUR']['Value'], 2)

            usd_text = f"💵Доллар: <b>{usd_rate}</b>"
            eur_text = f"💶Евро: <b>{eur_rate}</b>"

            return usd_text, eur_text
