import pandas as pd
from bs4 import BeautifulSoup
import requests
from datetime import datetime
from html_table_parser import parser_functions as parser
import collections
import re

# --- collections 오류 방지 ---
if not hasattr(collections, 'Callable'):
    collections.Callable = collections.abc.Callable


# DRAM Spot Price
def DRAM_Spot_Price():
    url = 'https://www.dramexchange.com/'
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    data = soup.select('#tb_NationalDramSpotPrice')
    p = parser.make2d(data[0])
    data = pd.DataFrame(p)
    data.columns = data.iloc[0]
    data.drop(0, inplace=True)
    date = soup.select_one('#NationalDramSpotPrice_show_day > span')
    date = date.text
    date = date[13:33]
    data['Update Time'] = date
    data.apply(pd.to_numeric, errors='ignore')
    return data


# Flash Spot Price
def Flash_Spot_Price():
    url = 'https://www.dramexchange.com/'
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    data = soup.select('#tb_NationalFlashSpotPrice')
    p = parser.make2d(data[0])
    data = pd.DataFrame(p)
    data.columns = data.iloc[0]
    data.drop(0, inplace=True)
    date = soup.select_one('#NationalFlashSpotPrice_show_day > span')
    date = date.text
    date = date[13:33]
    data['Update Time'] = date
    data.apply(pd.to_numeric, errors='ignore')
    return data

# Flash Spot Price
def wafer_spot_price():
    url = "https://www.dramexchange.com/"  # 실제 URL로 교체 필요
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    # --- "Last Update:" 문자열이 포함된 span 탐색 ---
    update_time = None
    for span in soup.find_all('span'):
        if span.get_text(strip=True).startswith('Last Update:'):
            text = span.get_text(strip=True)
            match = re.search(r'Last Update:([A-Za-z]+\.\d+\s+\d+\s+\d+:\d+)', text)
            if match:
                update_time = match.group(1)
                break

    # --- 테이블 파싱 ---
    table = soup.find('tbody', {'id': 'tb_ModuleSpotPrice'}) or soup.find('tbody', {'id': 'tb_NationalDramSpotPrice'})
    if not table:
        print("❌ 테이블을 찾을 수 없습니다.")
        return None

    rows = table.find_all('tr')
    data = []
    for row in rows[1:]:  # 첫 번째는 헤더
        cols = row.find_all('td')
        if len(cols) < 8:
            continue

        item = cols[0].get_text(strip=True)
        weekly_high = cols[1].get_text(strip=True)
        weekly_low = cols[2].get_text(strip=True)
        session_high = cols[3].get_text(strip=True)
        session_low = cols[4].get_text(strip=True)
        session_avg = cols[5].get_text(strip=True)
        avg_change = cols[6].get_text(strip=True)

        data.append([
            item, weekly_high, weekly_low, session_high, session_low,
            session_avg, avg_change, update_time
        ])

    df = pd.DataFrame(data, columns=[
        'Item', 'Weekly High', 'Weekly Low', 'Session High',
        'Session Low', 'Session Average', 'Average Change', 'Update Time'
    ])
    df = df.rename(columns={'Average Change':'Session Change'})
    return df


# 메인 실행
if __name__ == "__main__":
    print("="*60)
    print("DRAM & Flash 가격 데이터 수집 시작")
    print("="*60)
    
    # 오늘 날짜
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"수집 날짜: {today}")
    
    # 기존 데이터 불러오기
    try:
        existing_data = pd.read_excel('DRAMeXchange_Semi_price.xlsx')
        print(f"기존 데이터 로드: {len(existing_data)}개 항목")
        
        # 저장 날짜 컬럼이 없으면 추가
        if 'Save Date' not in existing_data.columns:
            existing_data['Save Date'] = None
            print("'Save Date' 컬럼 추가")
        
        # 오늘 날짜로 이미 저장된 데이터가 있는지 확인
        today_data = existing_data[existing_data['Save Date'] == today]
        
        if len(today_data) > 0:
            print(f"\n⚠️  오늘({today}) 이미 데이터가 수집되었습니다.")
            print(f"   기존 수집 항목 수: {len(today_data)}개")
            print("\n프로그램을 종료합니다. (하루에 한 번만 수집 가능)")
            exit()
        else:
            print(f"✓ 오늘 날짜 데이터 없음 - 수집 진행")
            
    except FileNotFoundError:
        existing_data = pd.DataFrame()
        print("새 파일 생성")
    
    # 데이터 수집
    print("\n데이터 수집 중...")
    df = pd.DataFrame()
    
    a = DRAM_Spot_Price()
    print(f"  DRAM Spot Price: {len(a)}개 항목")
    
    b = Flash_Spot_Price()
    print(f"  Flash Spot Price: {len(b)}개 항목")
    
    c = wafer_spot_price()
    print(f"  Flash Spot Price: {len(c)}개 항목")

    df = pd.concat([df, a, b, c])
    
    # 데이터 전처리
    df['Session Change'] = df['Session Change'].str.replace('%', '', regex=True)
    df = df.apply(pd.to_numeric, errors='ignore')
    df = df.drop(columns=['History','Daily High','Daily Low','Session High','Session Low','Weekly High','Weekly Low'], errors='ignore')

    # 저장 날짜 추가
    df['Save Date'] = today
    
    print(f"\n총 수집된 데이터: {len(df)}개")
    
    # 데이터 병합
    merged_data = pd.concat([existing_data, df], ignore_index=True)
    
    
    # NaN 제거 (Item이 없는 행 제거)
    merged_data = merged_data.dropna(subset=['Item'])
    
    # 중복 제거: Item과 Save Date 기준
    before_count = len(merged_data)
    merged_data = merged_data.drop_duplicates(subset=['Item', 'Save Date'], keep='last')
    after_count = len(merged_data)
    
    if before_count > after_count:
        print(f"중복 제거: {before_count - after_count}개 항목 제거됨")
    
    # 날짜순 정렬
    merged_data = merged_data.sort_values('Save Date', ascending=False)
    
    # 엑셀 저장
    merged_data.to_excel('DRAMeXchange_Semi_price.xlsx', index=False)
    
    print(f"\n{'='*60}")
    print(f"✓ 저장 완료!")
    print(f"  파일명: DRAMeXchange_Semi_price.xlsx")
    print(f"  총 저장 데이터: {len(merged_data)}개")
    print(f"  오늘 추가된 데이터: {len(df)}개")
    print(f"{'='*60}")
    
    # 최근 5일 데이터 요약
    print("\n최근 수집 날짜:")
    recent_dates = merged_data['Save Date'].unique()[:5]
    for date in recent_dates:
        count = len(merged_data[merged_data['Save Date'] == date])
        print(f"  {date}: {count}개 항목")