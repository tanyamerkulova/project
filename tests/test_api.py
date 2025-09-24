import pytest
import allure
from project.pages.api_page import AviasalesApi
from config.test_data import BASE_URL_API, TOKEN


@pytest.fixture(scope="module")
def api():
    return AviasalesApi(base_url=BASE_URL_API, token=TOKEN)


@pytest.mark.api
@allure.title("Поиск билетов из Москвы в СПб с фильтром по цене")
def test_search_tickets_by_price_range(api):
    response = api.search_by_price_range("MOW", "LED", 1000, 2000)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.api
@allure.title("Авиабилеты на определенные даты")
def test_get_ticket_prices_for_dates(api):
    response = api.prices_for_dates("MOW", "LON", "2025-07", "2025-08")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data


@pytest.mark.api
@allure.title("Получение курса валют к рублю")
def test_currency_rates(api):
    response = api.get_currency_rates()
    assert response.status_code == 200
    data = response.json()
    # Проверяем, что вернулся словарь
    assert isinstance(data, dict)
    # Проверяем, что есть популярные валюты
    for currency in ["usd", "eur", "gbp"]:
        assert currency in data, f"В ответе нет курса {currency.upper()}"
        assert isinstance(data[currency], (int, float)), \
            f"Курс {currency.upper()} не число"


@pytest.mark.api
@allure.title("Запрос без токена возвращает 401")
def test_request_without_token(api):
    response = api.get_latest_prices("MOW", "LED", token="")
    assert response.status_code == 401


@pytest.mark.api
@allure.title("Поиск с несуществующими IATA-кодами(origin, destination)\
               возвращает 400")
def test_invalid_iata_codes(api):
    response = api.get_latest_prices("ZZZ", "XXX", token=TOKEN)
    assert response.status_code == 400
