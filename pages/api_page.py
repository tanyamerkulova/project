import requests
import allure


class AviasalesApi:
    def __init__(self, base_url, token=None):
        self.base_url = base_url
        self.token = token

    @allure.step("API. Поиск билетов из {origin} в {destination}\
                  в пределах цены {value_min}-{value_max}")
    def search_by_price_range(self, origin, destination,
                              value_min=1000, value_max=2000):
        url = f"{self.base_url}/aviasales/v3/search_by_price_range"
        params = {
            "origin": origin,
            "destination": destination,
            "value_min": value_min,
            "value_max": value_max,
            "one_way": "true",
            "direct": "false",
            "locale": "ru",
            "currency": "rub",
            "market": "ru",
            "limit": 30,
            "page": 1,
            "token": self.token
        }
        return requests.get(url, params=params)

    @allure.step("API. Авиабилеты на даты {departure_at} - {return_at}")
    def prices_for_dates(self, origin, destination, departure_at, return_at):
        url = f"{self.base_url}/aviasales/v3/prices_for_dates"
        params = {
            "origin": origin,
            "destination": destination,
            "departure_at": departure_at,
            "return_at": return_at,
            "sorting": "price",
            "direct": "false",
            "cy": "usd",
            "limit": 30,
            "page": 1,
            "one_way": "true",
            "token": self.token
        }
        return requests.get(url, params=params)

    @allure.step("API. Получить курсы валют")
    def get_currency_rates(self):
        url = "http://yasen.aviasales.ru/adaptors/currency.json"
        return requests.get(url)

    @allure.step("API. Запрос последних цен с токеном {token}")
    def get_latest_prices(self, origin, destination, token):
        url = f"{self.base_url}/v2/prices/latest"
        params = {"origin": origin, "destination": destination,
                  "currency": "rub", "token": token}
        return requests.get(url, params=params)
