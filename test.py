from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import time

# ========================
# 1️⃣ 크롬 옵션 설정
# ========================
options = Options()
# 브라우저 창 숨기고 싶으면 주석 해제
# options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

# 드라이버 실행
driver = webdriver.Chrome(options=options)

# ========================
# 2️⃣ Tripod 월별 매출 페이지 접속
# ========================
url = "https://emops.twse.com.tw/server-java/t146sb05_e?co_id=3044&TYPEK=sii&step=0"
driver.get(url)
time.sleep(2)  # 페이지 로딩 대기

# ========================
# 3️⃣ Tripod More 버튼 클릭
# ========================
buttons = driver.find_elements(By.CLASS_NAME, "more_button")
for btn in buttons:
    onclick_attr = btn.get_attribute("onclick")
    if "ENGLISH_ABBR_NAME.value='Tripod'" in onclick_attr:
        btn.click()  # Tripod 버튼 클릭
        break

time.sleep(2)  # 새 창 로딩 대기

# ========================
# 4️⃣ 새 창으로 전환
# ========================
original_window = driver.current_window_handle
for handle in driver.window_handles:
    if handle != original_window:
        driver.switch_to.window(handle)
        break

# ========================
# 5️⃣ 새 창 HTML 파싱 및 테이블 추출
# ========================
soup = BeautifulSoup(driver.page_source, "html.parser")
table = soup.find("table")
if not table:
    raise Exception("테이블을 찾을 수 없습니다.")

# 테이블 행 읽기
rows = []
for tr in table.find_all("tr"):
    row = [td.get_text(strip=True) for td in tr.find_all(["td","th"])]
    if row:
        rows.append(row)

# DataFrame 변환
df = pd.DataFrame(rows[1:], columns=rows[0])
print(df.head())

# ========================
# 6️⃣ 새 창 닫고 원래 창 복귀
# ========================
driver.close()
driver.switch_to.window(original_window)

# ========================
# 7️⃣ 드라이버 종료
# ========================
driver.quit()

# ========================
# 8️⃣ CSV 저장 (선택)
# ========================
df.to_csv("tripod_monthly_revenue.csv", index=False, encoding="utf-8-sig")
print("월별 매출 데이터 저장 완료: tripod_monthly_revenue.csv")
