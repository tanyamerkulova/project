import allure
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from project.pages.search_page import SearchPage
from typing import List
from config.test_data import BASE_URL_UI


# ================= FIXTURE =================
@pytest.fixture(scope="module")
def driver():
    """
    Создает экземпляр Chrome WebDriver на весь модуль,
    чтобы ускорить прогон всех тестов.
    """
    options = Options()
    options.add_argument("--log-level=3")  # подавляем лишние логи
    driver = webdriver.Chrome(service=ChromeService(
        ChromeDriverManager().install()), options=options)
    yield driver
    driver.quit()


# ================= ТЕСТ 1 =================
@pytest.mark.ui
@allure.title("Поиск авиабилетов с корректными параметрами")
@allure.description("Проверка, что поиск возвращает\
                     корректные результаты при правильных параметрах.")
@allure.feature("Поиск авиабилетов")
@allure.severity(allure.severity_level.CRITICAL)
def test_search_flights_valid_params(driver):
    """
    Проверка поиска рейсов с корректными параметрами.
    """
    search_page = SearchPage(driver, BASE_URL_UI)

    with allure.step("Открыть страницу поиска"):
        search_page.open()

    with allure.step("Ввести параметры поиска"):
        search_page.set_from_city("Москва")
        search_page.set_to_city("Пермь")

    with allure.step("Выбрать дату"):
        search_page.set_date()

    with allure.step("Проверить, что есть результаты"):
        results: List = search_page.get_search_results()
        assert len(results) > 0, "Результаты поиска не найдены!"

    with allure.step("Проверить маршрут первого результата"):
        origin, destination = search_page.get_first_result_route()
        assert "Москва" in origin, f"Ожидалось 'Москва', но найдено '{origin}'"
        assert "Пермь" in destination, f"Ожидалось 'Пермь',\
              но найдено '{destination}'"


# ================= ТЕСТ 2 =================
@pytest.mark.ui
@allure.title("Поиск авиабилетов с пустыми полями")
@allure.description("Проверка, что при попытке поиска\
                     без заполнения полей отображается ошибка.")
@allure.feature("Поиск авиабилетов")
@allure.severity(allure.severity_level.CRITICAL)
def test_search_flights_empty_fields(driver):
    search_page = SearchPage(driver, BASE_URL_UI)

    with allure.step("Открыть страницу поиска"):
        search_page.open()

    with allure.step("Выполнить поиск без заполнения полей"):
        search_page.submit_search_without_fields()

    with allure.step("Проверить уведомления об обязательных полях"):
        errors = search_page.get_all_error_messages()
        assert any("укажите город" in e.lower() for e in errors), \
            f"Ошибка по городу не найдена: {errors}"
        assert any("укажите дату" in e.lower() for e in errors), \
            f"Ошибка по дате не найдена: {errors}"


# ================= ТЕСТ 3 =================
@pytest.mark.ui
@allure.title("Отображение подробной информации о рейсе")
@allure.feature("Поиск авиабилетов")
@allure.severity(allure.severity_level.CRITICAL)
def test_flight_details(driver):
    search_page = SearchPage(driver, BASE_URL_UI)

    with allure.step("Открыть страницу поиска и задать параметры"):
        search_page.open()
        search_page.set_from_city("Москва")
        search_page.set_to_city("Пермь")
        search_page.set_date()

    with allure.step("Открыть карточку рейса"):
        search_page.open_flight_card()

    with allure.step("Получить данные рейса и проверить их"):
        details = search_page.get_flight_card_details()
        assert details["origin"], "Не найден город отправления"
        assert details["destination"], "Не найден город назначения"
        assert details["departure_time"], "Не найдено время вылета"
        assert details["arrival_time"], "Не найдено время прилёта"
        assert details["price"], "Не найдена цена"


# ================= ТЕСТ 4 =================
@pytest.mark.ui
@allure.title("Сортировка авиабилетов по времени отправления")
@allure.description("Проверка, что рейсы отображаются\
                     в порядке возрастания времени отправления.")
@allure.feature("Поиск авиабилетов")
@allure.severity(allure.severity_level.CRITICAL)
def test_sort_by_departure_time(driver):
    search_page = SearchPage(driver, BASE_URL_UI)

    with allure.step("Открыть страницу поиска и задать параметры"):
        search_page.open()
        search_page.accept_cookies_if_present()
        search_page.set_from_city("Москва")
        search_page.set_to_city("Пермь")
        search_page.set_date()

    with allure.step("Сортировка по времени вылета"):
        search_page.open_sort_filter()
        search_page.sort_by_earliest_departure()

    with allure.step("Проверить, что рейсы отсортированы"):
        departure_times = search_page.get_departure_times()
        sorted_times = \
            search_page.sort_times_with_midnight_crossing(departure_times)
        assert departure_times == sorted_times, \
            f"Список рейсов не отсортирован: {departure_times}"


# ================= ТЕСТ 5 =================
@pytest.mark.ui
@allure.title("Отображение стоимости для нескольких пассажиров")
@allure.description("Проверка расчета стоимости билетов при\
                     увеличении числа пассажиров")
@allure.feature("Фильтрация авиабилетов")
@allure.severity(allure.severity_level.CRITICAL)
def test_filter_by_price(driver):
    search_page = SearchPage(driver, BASE_URL_UI)

    with allure.step("Открыть страницу поиска и задать параметры"):
        search_page.open()
        search_page.set_from_city("Москва")
        search_page.set_to_city("Пермь")
        search_page.set_date()

    with allure.step("Получить стоимость для 1 пассажира"):
        search_page.set_adult_passengers(1)
        prices_1 = search_page.get_ticket_prices()

    with allure.step("Получить стоимость для 3 пассажиров"):
        search_page.set_adult_passengers(3)
        prices_3 = search_page.get_ticket_prices()

    with allure.step("Проверить корректность расчета цен"):
        avg_price_1 = sum(prices_1) / len(prices_1)
        avg_price_3 = sum(prices_3) / len(prices_3)
        assert avg_price_3 >= avg_price_1 * 3, (
            f"Средняя цена для 3 пассажиров ({avg_price_3}) "
            f"меньше 3 * средней цены для 1 ({avg_price_1})")
