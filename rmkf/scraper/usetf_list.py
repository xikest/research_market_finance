from bs4 import BeautifulSoup
import pandas as pd
import time
from tqdm import tqdm
from ._scaper_scheme import Scraper

class USETF_LIST(Scraper):
    def __init__(self, enable_headless=True, wait_time=1):
        super().__init__(enable_headless=enable_headless)
        self.wait_time = wait_time
        self.base_url = "https://etfdb.com/screener/"

    def _get_etf_info(self, url:str) -> pd.DataFrame:

        # 웹 드라이버 가져오기
        driver = self.web_driver.get_chrome()
        try:
            # 웹 페이지 요청
            driver.get(url)
            time.sleep(self.wait_time)  # 페이지 로딩 대기

            # 페이지 소스 가져오기
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            content_div = soup.find('div', class_='bootstrap-table screener-table-overview')
            thead = content_div.find('thead')
            # 테이블 헤더 추출
            headers = []
            for th in thead.find_all('th'):
                # span = th.find('span', class_='full-label')
                # if span:
                #     headers.append(span.get_text(strip=True).lower())
                # else:
                headers.append(th.get_text(strip=True).lower())  # Fallback to text if span not found

            # 테이블 데이터 추출
            tbody = content_div.find('tbody')
            rows = []
            for tr in tbody.find_all('tr'):
                cells = tr.find_all('td')
                row = [cell.get_text(strip=True) for cell in cells]
                rows.append(row)
            return pd.DataFrame(rows, columns=headers)
        finally:
            driver.quit()

    def get_etf_list(self) -> pd.DataFrame:
        etf_df = pd.DataFrame()
        for page in tqdm(range(1, 137)):
            url = f"{self.base_url}#page={page}"
            page_df = self._get_etf_info(url)
            if page_df is None:
                break
            etf_df = pd.concat([etf_df, page_df], ignore_index=True)
        return etf_df