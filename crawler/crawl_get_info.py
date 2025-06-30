from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import psycopg2
import requests
import csv
from selenium.webdriver.chrome.options import Options

def main():
    print("*크롤링을 시작합니다*")

    valid_categories = {
        "로맨스", "로판", "SF/판타지", "일상/현대", "무협", "시대",
        "BL", "GL", "남성향", "기타", "1:1 롤플레잉", "시뮬레이션", "여성향", "전체"
    }

    conn = psycopg2.connect(
        host="postgres",
        dbname="postgres",
        user="donghyeokpark",
        password="airflow",
    )
    cur = conn.cursor()

    def create_tables():
        cur.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                image BYTEA,
                first_message TEXT,
                category_names TEXT,
                CONSTRAINT unique_name UNIQUE (name)
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                CONSTRAINT categories_name_key UNIQUE (name)
            );
        """)
        conn.commit()

    def reset_tables():
        cur.execute("TRUNCATE TABLE characters RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE categories RESTART IDENTITY CASCADE;")
        conn.commit()

    create_tables()
    reset_tables()

    def insert_character(name, description, image, first_message, category_names):
        cur.execute("""
            INSERT INTO characters (name, description, image, first_message, category_names)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (name) DO NOTHING
        """, (name, description, image, first_message, category_names))
        conn.commit()

    def insert_category(name):
        cur.execute("""
            INSERT INTO categories (name) VALUES (%s)
            ON CONFLICT (name) DO NOTHING
        """, (name,))
        conn.commit()

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.binary_location = "/usr/bin/chromium"

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://crack.wrtn.ai/")
    time.sleep(3)

    category_buttons = driver.find_elements(By.CSS_SELECTOR, ".swiper-wrapper button")

    for i, button in enumerate(category_buttons[3:]):
        try:
            category_name = button.find_element(By.TAG_NAME, "p").text.strip()
            print(f"\n[{i+1}] 카테고리: {category_name}")
            driver.execute_script("arguments[0].click();", button)
            time.sleep(2.5)

            scroll_area = driver.find_element(By.ID, "character-home-scroll")
            last_height = driver.execute_script("return arguments[0].scrollHeight", scroll_area)

            scroll_attempts = 0
            max_attempts = 3

            while scroll_attempts <= max_attempts:
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_area)
                time.sleep(2.5)
                new_height = driver.execute_script("return arguments[0].scrollHeight", scroll_area)
                if new_height == last_height:
                    break
                last_height = new_height
                scroll_attempts += 1

            cards = driver.find_elements(By.CSS_SELECTOR, ".css-il3plt .css-m2oo7f")
            print(f"{len(cards)}개의 캐릭터 카드 발견")

            for idx, _ in enumerate(cards):
                try:
                    print("##### 캐릭터 정보 ######")
                    time.sleep(0.3)
                    cards = driver.find_elements(By.CSS_SELECTOR, ".css-il3plt .css-m2oo7f")
                    card = cards[idx]
                    driver.execute_script("arguments[0].click();", card)

                    wait = WebDriverWait(driver, 5)
                    modal = wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "div.character-info-modal-content-body")))

                    name = modal.find_element(By.CSS_SELECTOR, "p.css-132a3j1").text.strip()
                    description = modal.find_element(By.CSS_SELECTOR, "p.css-nybeci").text.strip()
                    img_url = driver.find_element(By.CSS_SELECTOR, "img[alt='character_thumbnail']").get_attribute("src")
                    img = requests.get(img_url).content

                    print(f"이름: {name}")
                    print(f"설명: {description}")
                    print(f"이미지: {img}")

                    category_p_tags = modal.find_elements(By.CSS_SELECTOR, 'div.css-lwph31 p.css-1cgy0px')
                    raw_categories = [p.text.strip() for p in category_p_tags if p.text.strip()]
                    filtered_categories = list({cat for cat in raw_categories if cat in valid_categories})

                    for cat in filtered_categories:
                        insert_category(cat)

                    category_names = ",".join(filtered_categories)
                    print(f"카테고리: {category_names}")

                    chat_btn = wait.until(EC.element_to_be_clickable(
                        (By.XPATH, "//*[@id=\"web-modal\"]/div/div/div/div/div[4]/button")))
                    actions = ActionChains(driver)
                    actions.key_down(Keys.COMMAND).click(chat_btn).key_up(Keys.COMMAND).perform()

                    WebDriverWait(driver, 5).until(lambda d: len(d.window_handles) > 1)
                    new_tab = [w for w in driver.window_handles if w != driver.current_window_handle][0]
                    driver.switch_to.window(new_tab)
                    time.sleep(2.5)

                    try:
                        understand_btn = driver.find_element(By.XPATH, "//*[@id=\"web-modal\"]/div/div/div/div/div[2]/button")
                        driver.execute_script("arguments[0].click();", understand_btn)
                        time.sleep(1)
                    except NoSuchElementException:
                        pass

                    time.sleep(2.5)
                    try:
                        first_message = driver.find_element(By.CSS_SELECTOR, "div.css-jswf15").text.strip()
                        print(f"첫 메시지: {first_message[:30]}...")
                    except NoSuchElementException:
                        first_message = ""
                        print("첫 메시지 없음")

                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

                    try:
                        insert_character(name, description, img, first_message, category_names)
                    except Exception as e:
                        print("캐릭터 저장 실패:", e)
                        conn.rollback()

                except Exception as e:
                    print(f"카드 파싱 실패: {e}")

        except Exception as e:
            print(f"카테고리 처리 실패: {e}")

    driver.quit()

    # characters.csv 저장
    cur.execute("SELECT * FROM characters")
    columns = [desc[0] for desc in cur.description]
    with open("/opt/airflow/data/characters.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(cur.fetchall())
    print("characters.csv 저장 완료")

    # categories.csv 저장
    cur.execute("SELECT * FROM categories")
    category_columns = [desc[0] for desc in cur.description]
    with open("/opt/airflow/data/categories.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(category_columns)
        writer.writerows(cur.fetchall())
    print("categories.csv 저장 완료")

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
