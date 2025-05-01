from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import time
import os
import requests

# 크롬 드라이버 초기화
driver = webdriver.Chrome()
driver.maximize_window() # 창 최대화

# 크림 사이트로 이동
url = 'https://kream.co.kr/search?keyword=%EC%9A%B4%EB%8F%99%ED%99%94'
driver.get(url)

# try:
#     # 인기순 버튼을 클릭합니다.
#     popular_sort_button = WebDriverWait(driver, 10).until(
#         EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '인기순')]"))
#     )
#     popular_sort_button.click()
#     print("인기순으로 정렬 버튼을 클릭했습니다.")
    
#     # 프리미엄 높은순 버튼을 클릭합니다.
#     premium_sort_button = driver.find_element(By.CSS_SELECTOR, 'div.filter_sorting > ul > li:nth-child(4) > a > div > p')
#     premium_sort_button.click()
#     print("프리미엄 높은순으로 상품을 정렬합니다.")

# except NoSuchElementException as e:
#     print("버튼을 찾을 수 없습니다.")


max_scroll_height = 1000000  # 원하는 최대 스크롤 높이 1000000

# 스크롤을 페이지의 끝까지 내립니다. 
while True:
    try:
        last_height = driver.execute_script("return document.body.scrollHeight")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)

        WebDriverWait(driver, 20).until(
            lambda driver: driver.execute_script("return document.body.scrollHeight") > last_height)
        new_height = driver.execute_script("return document.body.scrollHeight")

        # if new_height == last_height:
        #     print("end of height")
        #     break
        if new_height >= max_scroll_height:
        # 스크롤이 원하는 최대 높이를 넘으면 반복문을 종료합니다.
            print("end of height")
            break
        
        last_height = new_height
        print("last_height: ", last_height)
        print("-------------------------")

    except TimeoutException:
        print("Timeout 에러 발생! 다시 시도합니다.")
        continue

# 현재 페이지의 HTML을 가져와 BeautifulSoup 객체를 생성합니다.
html = driver.page_source
soup_all = BeautifulSoup(html, 'lxml')

# 크롬 드라이버를 종료합니다.
driver.quit()

# 크롬 드라이버 종료 후에도 사용할 변수 초기화
url_list = []

# 고유 제품 코드(5-6자리 숫자)를 추출합니다.
shoe_tags = soup_all.find_all('div', class_='product_card')
shoe_ids = []

for shoe in shoe_tags:
    href_tag = shoe.find('a')
    if href_tag:
        href = href_tag['href']
        shoe_id = href.split('/products/')[1]
        shoe_ids.append(shoe_id)
        
# 제품 코드를 URL 형식에 붙여 고유 URL을 생성합니다.
for id in shoe_ids:
    code = id
    url = f"https://kream.co.kr/products/{code}"
    url_list.append(url)

# URL에서 HTML 정보를 파싱합니다.
print("HTML 정보 파싱 중")
html = []

for url in url_list:
    req = requests.get(url, headers={'User-agent':'Mozilla/5.0'})
    soup = BeautifulSoup(req.text, "lxml")
    html.append(soup)

# 데이터프레임을 생성합니다.
df = pd.DataFrame(columns=['name_k', 'brand', 'price_recent', 'num_model','date', 'color', 'price_0'])

# HTML에서 필요한 정보를 추출합니다.
for soup in html:
    try:
        name_k = soup.find("p", attrs={"class":"sub-title"})
        name_k_text = name_k.text if name_k else ""

        price_recent = soup.find("span", attrs={"class":"price-info"})
        price_recent_text = price_recent.text if price_recent else ""

        info = soup.find_all("div", attrs={"class" : "product_info"})

        brand = soup.find("p", attrs={"class" : "text-lookup title-text display_paragraph action_url" })
        brand_text = brand.text if brand else ""

        model_num = info[1].text if info and len(info) >= 2 else ""

        date = info[2].text if info and len(info) >= 2 else ""

        color = info[3].text if info and len(info) >= 3 else ""
        
        price_0 = info[0].text if info and len(info) >= 4 else ""
        
        data = [name_k_text, brand_text, price_recent_text, model_num, date, color, price_0]
        
        df = pd.concat([df, pd.DataFrame([data], columns=df.columns)], ignore_index=True)
    
    except AttributeError as e:
        print(f"An error occurred: {e}")

# 결측치 처리를 위해 빈 값이 있는 행을 제거합니다.
df['name_k'] = df['name_k'].replace('', np.nan)
df.dropna(inplace=True)

# 현재 파일의 경로를 가져옵니다.
current_path = os.path.dirname(os.path.abspath(__file__))

# 결과를 파일로 저장합니다.
df.to_csv(os.path.join(current_path, 'kream_data.csv'), index=False)