import pandas as pd
from bs4 import BeautifulSoup
import requests
from datetime import datetime
from html_table_parser import parser_functions as parser
import collections
import re
import matplotlib.pyplot as plt

if not hasattr(collections, 'Callable'):
    collections.Callable = collections.abc.Callable

# -------------------- 데이터 수집 함수 --------------------
def DRAM_Spot_Price():
    url = 'https://www.dramexchange.com/'
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    data = soup.select('#tb_NationalDramSpotPrice')
    p = parser.make2d(data[0])
    data = pd.DataFrame(p)
    data.columns = data.iloc[0]
    data.drop(0, inplace=True)
    date = soup.select_one('#NationalDramSpotPrice_show_day > span').text[13:33]
    data['Update Time'] = date
    data.apply(pd.to_numeric, errors='ignore')
    return data

def Flash_Spot_Price():
    url = 'https://www.dramexchange.com/'
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    data = soup.select('#tb_NationalFlashSpotPrice')
    p = parser.make2d(data[0])
    data = pd.DataFrame(p)
    data.columns = data.iloc[0]
    data.drop(0, inplace=True)
    date = soup.select_one('#NationalFlashSpotPrice_show_day > span').text[13:33]
    data['Update Time'] = date
    data.apply(pd.to_numeric, errors='ignore')
    return data

def wafer_spot_price():
    url = "https://www.dramexchange.com/"
    res = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    update_time = None
    for span in soup.find_all('span'):
        if span.get_text(strip=True).startswith('Last Update:'):
            match = re.search(r'Last Update:([A-Za-z]+\.\d+\s+\d+\s+\d+:\d+)', span.get_text(strip=True))
            if match:
                update_time = match.group(1)
                break
    table = soup.find('tbody', {'id':'tb_ModuleSpotPrice'}) or soup.find('tbody', {'id':'tb_NationalDramSpotPrice'})
    if not table:
        print("❌ 테이블을 찾을 수 없습니다.")
        return None
    data = []
    for row in table.find_all('tr')[1:]:
        cols = row.find_all('td')
        if len(cols) < 8:
            continue
        data.append([
            cols[0].get_text(strip=True),
            cols[1].get_text(strip=True),
            cols[2].get_text(strip=True),
            cols[3].get_text(strip=True),
            cols[4].get_text(strip=True),
            cols[5].get_text(strip=True),
            cols[6].get_text(strip=True),
            update_time
        ])
    df = pd.DataFrame(data, columns=[
        'Item','Weekly High','Weekly Low','Session High','Session Low','Session Average','Average Change','Update Time'
    ])
    df = df.rename(columns={'Average Change':'Session Change'})
    return df

# -------------------- 그래프 함수 --------------------
def plot_ddr5_graph(df, item_name="DDR5 16G (2Gx8) 4800/5600", save_path="DDR5_16G.png"):
    try:
        item_df = df[df['Item'] == item_name].copy()
        if item_df.empty:
            print(f"⚠️ {item_name} 데이터 없음")
            return

        item_df['Save Date'] = pd.to_datetime(item_df['Save Date'], errors='coerce')
        item_df = item_df.sort_values('Save Date')
        item_df['Save Date_str'] = item_df['Save Date'].dt.strftime('%Y%m%d')

        fig, ax1 = plt.subplots(figsize=(10,5))

        ax1.plot(item_df['Save Date_str'], item_df['Session Average'], color='blue', marker='o', label='Average')
        ax1.set_xlabel('Save Date')
        ax1.set_ylabel('Session Average', color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')

        ax2 = ax1.twinx()
        ax2.bar(item_df['Save Date_str'], item_df['Session Change'], color='navy', alpha=0.3, label='Change(%)')
        ax2.set_ylabel('Session Change (%)', color='navy')
        ax2.tick_params(axis='y', labelcolor='navy')

        # 범례 합치기
        lines_labels = [ax.get_legend_handles_labels() for ax in [ax1, ax2]]
        lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
        ax1.legend(lines, labels, loc='upper left')

        # x축 라벨 90도 회전
        ax1.tick_params(axis='x', rotation=90)

        plt.title(f'{item_name} Price Trend')
        fig.tight_layout()

        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"✅ 그래프 저장 완료: {save_path}")

    except Exception as e:
        print(f"❌ 그래프 생성 중 오류 발생: {e}")



# -------------------- 메인 --------------------
if __name__=="__main__":
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"수집 날짜: {today}")
    
    try:
        merged_data = pd.read_excel('DRAMeXchange_Semi_price.xlsx')
        if 'Save Date' not in merged_data.columns:
            merged_data['Save Date'] = None
        print(f"기존 데이터 로드: {len(merged_data)}개 항목")
    except FileNotFoundError:
        merged_data = pd.DataFrame()
        print("엑셀 파일 없음, 새로 생성")
    
    # 오늘 데이터가 이미 있으면 수집 생략
    today_data = merged_data[merged_data['Save Date']==today] if not merged_data.empty else pd.DataFrame()
    
    if today_data.empty:
        print("오늘 데이터 없음 - 새로 수집")
        df_new = pd.concat([DRAM_Spot_Price(), Flash_Spot_Price(), wafer_spot_price()])
        df_new['Session Change'] = df_new['Session Change'].str.replace('%','', regex=True)
        df_new = df_new.apply(pd.to_numeric, errors='ignore')

        # 불필요한 컬럼 제거
        df_new = df_new.drop(columns=['History','Daily High','Daily Low','Session High',
                                      'Session Low','Weekly High','Weekly Low'], errors='ignore')

        df_new['Save Date'] = today
        merged_data = pd.concat([merged_data, df_new], ignore_index=True)
        merged_data = merged_data.dropna(subset=['Item'])
        merged_data = merged_data.drop_duplicates(subset=['Item','Save Date'], keep='last')
        merged_data = merged_data.sort_values('Save Date', ascending=False)
        merged_data.to_excel('DRAMeXchange_Semi_price.xlsx', index=False)
        print(f"✅ 오늘 데이터 수집 완료, 엑셀 저장")
    else:
        print("오늘 데이터 이미 존재 - 수집 생략")
    
    # 그래프 생성
    plot_ddr5_graph(merged_data)
