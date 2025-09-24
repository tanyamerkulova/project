from time import sleep
import allure
import re
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import List, Tuple, Dict, Optional
from datetime import datetime, timedelta, date


class SearchPage:
    def __init__(self, driver, base_url: str):
        """
        :param driver: экземпляр Selenium WebDriver
        :param base_url: базовый URL сайта
        """
        self.driver = driver
        self.wait = WebDriverWait(driver, 30)
        self.base_url = base_url.rstrip("/")

    # ================= ОТКРЫТИЕ СТРАНИЦЫ =================
    @allure.step("Открыть страницу поиска авиабилетов")
    def open(self) -> None:
        """Открывает базовую страницу поиска авиабилетов"""
        self.driver.get(f"{self.base_url}")

    # ================= ПОЛЯ ГОРОДОВ =================
    @allure.step("Ввести город отправления: {from_city}")
    def set_from_city(self, from_city: str) -> None:
        """
        Вводит город отправления в поле поиска

        Args:
            from_city (str): название города отправления
        """
        field = self.driver.find_element(
            By.XPATH, '//*[@id="avia_form_origin-input"]')
        field.click()
        current_value = field.get_attribute("value")
        for _ in range(len(current_value)):
            field.send_keys(Keys.BACKSPACE)
        self.wait.until(lambda d: d.find_element
                        (By.ID, "avia_form_origin-input"
                         ).get_attribute("value") == "")
        field.send_keys(from_city)


# ждём, чтобы значение закрепилось
        self.wait.until(
            lambda d: d.find_element
            (By.ID, "avia_form_origin-input").get_attribute("value")
            == from_city)
        sleep(2)

    @allure.step("Ввести город назначения: {to_city}")
    def set_to_city(self, to_city: str, retries: int = 2) -> None:
        """
        Вводит город назначения и ожидает обновления страницы

        Args:
            to_city (str): название города назначения
            retries (int): количество попыток на случай проблем с обновлением
        """
        for attempt in range(retries):
            field = self.driver.find_element(
                By.XPATH, '//*[@id="avia_form_destination-input"]')
            field.click()
            current_value = field.get_attribute("value")
            for _ in range(len(current_value)):
                field.send_keys(Keys.BACKSPACE)
            field.send_keys(to_city)
            self.wait.until(lambda d: d.find_element(
                By.XPATH, '//*[@id="avia_form_destination-input"]'
                ).get_attribute("value") == to_city)
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH,
                         '//h2[@data-test-id="text" \
                            and text()="График цен"]')))
                return
            except Exception:
                if attempt < retries - 1:
                    print(f"Попытка {attempt+1} неудачна, пробуем ещё раз...")
                    sleep(2)
                else:
                    raise RuntimeError("Страница не обновилась\
                                        после ввода города назначения")

# ================= ДАТА =================
    @allure.step("Выбрать дату вылета")
    def set_date(self) -> None:
        """Выбирает сегодняшнюю дату вылета и отправляет форму"""
        field = self.driver.find_element(By.CSS_SELECTOR,
                                         '[data-test-id="start-date-field"]')
        field.click()
        self.wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@data-test-id="dropdown"]')))
        sleep(1)
        btn = self.driver.find_element(
            By.CSS_SELECTOR, "[aria-label^='Today']")
        btn.click()
        sleep(1)
        self.driver.find_element(
            By.CSS_SELECTOR, '[data-test-id="form-submit"]').click()
        if len(self.driver.window_handles) > 1:
            self.driver.switch_to.window(self.driver.window_handles[1])

    # ================= РЕЗУЛЬТАТЫ =================
    @allure.step("Получить результаты поиска")
    def get_search_results(self) -> List:
        """Возвращает список найденных элементов билетов"""
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '[data-test-id^="ticket"]')))
        results = self.driver.find_elements(
            By.CSS_SELECTOR, '[data-test-id^="ticket"]')
        return results

    @allure.step("Получить маршрут первого результата")
    def get_first_result_route(self) -> Tuple[str, str]:
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'div[data-test-id="ticket-preview"]')))

        # получаем все карточки рейсов
        flights = self.driver.find_elements(
            By.CSS_SELECTOR, 'div[data-test-id="ticket-preview"]')
        if not flights:
            raise Exception("Рейсы не найдены на странице")

        first_flight = flights[0]  # первый результат

        # Первый сегмент — вылет
        departure_segment = first_flight.find_element(
            By.CSS_SELECTOR, "div.s__znjsAig6OswOqOsl.s__ArEb299EZ30wXeEL")
        departure_texts = departure_segment.find_elements(
            By.CSS_SELECTOR, "div[data-test-id='text']")
        origin = departure_texts[1].text.strip()  # город вылета

        # Второй сегмент — прилёт
        arrival_segment = first_flight.find_element(
            By.CSS_SELECTOR, "div.s__znjsAig6OswOqOsl.s__Vz8S7bOiF1EDe0z9")
        arrival_texts = arrival_segment.find_elements(
            By.CSS_SELECTOR, "div[data-test-id='text']")
        destination = arrival_texts[1].text.strip()  # город прилёта

        return origin, destination

    # ================= ПОИСК С ПУСТЫМИ ПОЛЯМИ =================
    @allure.step("Выполнить поиск с пустыми полями")
    def submit_search_without_fields(self) -> None:
        """Нажимает кнопку поиска без заполнения полей"""
        self.driver.find_element(
            By.CSS_SELECTOR, '[data-test-id="form-submit"]').click()

    @allure.step("Получить все уведомления об обязательных полях")
    def get_all_error_messages(self) -> List[str]:
        """Возвращает список текстов ошибок по обязательным полям"""
        self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@data-test-id="text"\
                  and (contains(text(), "Укажите город") \
                 or contains(text(), "Укажите дату"))]')))
        errors = self.driver.find_elements(
            By.XPATH, '//div[@data-test-id="text"\
                  and (contains(text(), "Укажите город")\
                      or contains(text(), "Укажите дату"))]')
        return [e.text.strip() for e in errors]

    def accept_cookies_if_present(self) -> None:
        """Закрывает баннер с cookie, если он есть"""
        try:
            cookie_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    '[data-test-id="accept-cookies-button"]')))
            cookie_btn.click()
            sleep(0.5)  # небольшая пауза, чтобы баннер исчез
        except Exception:
            pass  # баннера нет, пропускаем

    # ================= СОРТИРОВКА =================
    @allure.step("Открыть фильтр сортировки")
    def open_sort_filter(self) -> None:
        """Открывает фильтр сортировки"""
        sort_button = WebDriverWait(self.driver, 15).until(
            EC.visibility_of_element_located(
                (By.XPATH, './/div[@data-test-id="text"\
                  and contains(.,"Сортировка")]')))
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", sort_button)
        sleep(0.5)
        actions = ActionChains(self.driver)
        actions.move_to_element(sort_button).click().perform()

    @allure.step("Сортировать рейсы по времени отправления")
    def sort_by_earliest_departure(self) -> None:
        """Сортирует рейсы по времени вылета"""
        departure_sort = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                'div[data-test-id=\
                    "single-choice-filter-sort-departure_time_asc"]')))
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", departure_sort)
        departure_sort.click()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, 'div[data-test-id="ticket-preview"]')))
        sleep(2)

    def sort_times_with_midnight_crossing(
            self, times: List[datetime.time]) -> List[datetime.time]:
        """Сортировка списка времени с учётом перехода через полночь"""
        if not times:
            return []

        base_date = date.today()
        sorted_datetimes = []
        prev_dt = datetime.combine(base_date, times[0])
        sorted_datetimes.append(prev_dt)

        for t in times[1:]:
            curr_dt = datetime.combine(base_date, t)
            if curr_dt < prev_dt:
                curr_dt += timedelta(days=1)
            sorted_datetimes.append(curr_dt)
            prev_dt = curr_dt

        return [dt.time() for dt in sorted(sorted_datetimes)]

    def get_departure_times(self) -> List[datetime.time]:
        """Возвращает список времени отправления всех рейсов"""
        flights = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, 'div[data-test-id="ticket-preview"]')))
        times = []
        for flight in flights:
            departure_segment = flight.find_element(
                By.CSS_SELECTOR, 'div.s__znjsAig6OswOqOsl.s__ArEb299EZ30wXeEL')
            time_elements = departure_segment.find_elements(
                By.CSS_SELECTOR, 'div[data-test-id="text"]')
            for el in time_elements:
                text = el.text.strip()
                if re.match(r'^\d{2}:\d{2}$', text):
                    times.append(datetime.strptime(text, '%H:%M').time())
        return times

# ================= ЦЕНЫ =================
    @allure.step("Выбрать количество взрослых пассажиров: {adults}")
    def set_adult_passengers(self, adults: int = 1) -> None:
        """
        Устанавливает количество взрослых пассажиров и нажимает Найти билеты
        """
        passenger_field = self.driver.find_element(
            By.CSS_SELECTOR, '[data-test-id="passengers-field"]')
        passenger_field.click()
        sleep(1)
        adult_container = self.driver.find_element(
            By.CSS_SELECTOR, '[data-test-id="number-of-adults"]')
        count_el = adult_container.find_element(
            By.CSS_SELECTOR, '[data-test-id="passenger-number"]')
        current_count = int(count_el.text.strip())
        increase_btn = adult_container.find_element(
            By.CSS_SELECTOR, 'button[data-test-id="increase-button"]')
        decrease_btn = adult_container.find_element(
            By.CSS_SELECTOR, 'button[data-test-id="decrease-button"]')
        while current_count < adults:
            increase_btn.click()
            current_count += 1
            sleep(0.3)
        while current_count > adults:
            decrease_btn.click()
            current_count -= 1
            sleep(0.3)
        find_tickets_btn = self.driver.find_element(
            By.CSS_SELECTOR, 'button[data-test-id="form-submit"]')
        find_tickets_btn.click()

        WebDriverWait(self.driver, 20).until(
            EC.presence_of_all_elements_located((
                By.CSS_SELECTOR, 'div[data-test-id^="ticket"]')))
        # дождаться полной загрузки страницы
        WebDriverWait(self.driver, 30).until(
            lambda d: d.execute_script(
                "return document.readyState") == "complete")

    @allure.step("Получить все цены билетов")
    def get_ticket_prices(self) -> List[int]:
        """Возвращает список цен всех найденных билетов"""
        flights = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, 'div[data-test-id^="ticket"]')))
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '[data-test-id^="ticket"]')))

        prices = []
        for flight in flights:
            try:

                price_el = flight.find_element(
                    By.CSS_SELECTOR, 'div[data-test-id="price"]')
                text = price_el.text.strip()
                price_value = int(re.sub(r"[^\d]", "", text))
                prices.append(price_value)
            except Exception:
                continue
        return prices

    # ================= ПОДРОБНОСТИ РЕЙСА =================
    @allure.step("Открыть карточку рейса")
    def open_flight_card(self) -> None:
        """Открывает первую карточку рейса с безопасным кликом"""
        # Ждем появления карточек рейсов
        flights = WebDriverWait(self.driver, 30).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, 'div[data-test-id^="ticket"]')))

        if not flights:
            raise RuntimeError("Не удалось найти карточки рейсов!")

        first_flight = flights[0]

        # Прокрутка до элемента и клик через JS, чтобы избежать наложений
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", first_flight)
        sleep(0.5)
        try:
            # пробуем стандартный клик через ActionChains
            actions = ActionChains(self.driver)
            actions.move_to_element(first_flight).click().perform()
        except Exception:
            # если не получилось — кликаем через JS
            self.driver.execute_script("arguments[0].click();", first_flight)

    @allure.step("Получить данные из карточки рейса")
    def get_flight_card_details(self) -> Dict[str, Optional[str]]:
        """
        Возвращает словарь с деталями рейса.
        В случае отсутствия данных возвращает None.
        """
        details = {}
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '[data-test-id="ticket-modal-content"]')))

        try:
            details["airline"] = self.driver.find_element(
                By.XPATH, "//div[contains(@class,\
                    's__p2aZ_ALR52Mboq4a s__czWTXrMeAzlXSjEV\
                          s__NwaJc47i36olMXsl s__PrgITSqfz8pt81Gp')\
                              and @data-test-id='text']").text.strip()
        except Exception:
            details["airline"] = None

        try:
            details["departure_time"] = self.driver.find_element(
                By.CSS_SELECTOR, "div.s__ndfpzu1qInAbxnYA:first-child\
                      div[data-test-id='text']:first-child").text.strip()
            details["origin"] = self.driver.find_element(
                By.CSS_SELECTOR, "div.s__ndfpzu1qInAbxnYA:first-child\
                      div[data-test-id='text']:nth-child(2)").text.strip()
        except Exception:
            details["departure_time"] = details["origin"] = None

        try:
            details["arrival_time"] = self.driver.find_element(
                By.CSS_SELECTOR, "div.s__ndfpzu1qInAbxnYA:nth-child(2)\
                      div[data-test-id='text']:first-child").text.strip()
            details["destination"] = self.driver.find_element(
                By.CSS_SELECTOR, "div.s__ndfpzu1qInAbxnYA:nth-child(2)\
                      div[data-test-id='text']:nth-child(2)").text.strip()
        except Exception:
            details["arrival_time"] = details["destination"] = None

        try:
            details["price"] = self.driver.find_element(
                By.CSS_SELECTOR,
                '[data-test-id="proposal-0-title"]').text.strip()
        except Exception:
            details["price"] = None

        return details
