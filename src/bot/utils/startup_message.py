import asyncio
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

            return usd_rate, eur_rate

async def btc():
    url2 = "https://api.coindesk.com/v1/bpi/currentprice.json"

    async with aiohttp.ClientSession() as session:
        async with session.get(url2) as response2:
            btc_rate = await response2.text()

    return btc_rate
if __name__ == '__main__':
    btc = asyncio.run(btc())
    print(btc)