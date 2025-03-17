from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
from bs4 import BeautifulSoup
import time
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px 
from plotly.subplots import make_subplots
import plotly.io as pio
from datetime import datetime
from ._scaper_scheme import Scraper



class WISDOM_WHALE(Scraper):              
    def __init__(self, url:str = "https://whalewisdom.com/filer/berkshire-hathaway-inc", select_q:int=0, enable_headless:bool=True, wait_time=1, verbose=False):
        """
        intput_folder_path = "input",
        output_folder_path="results"
        """
        super().__init__(enable_headless=enable_headless)
        self.wait_time = wait_time
        
        self.intput_folder,self.output_folder = self._initialize_data_paths()
        self.title_q, self.data_df = self._get_holdings(url, select_q, verbose)
        self.current_date = datetime.now().strftime("%Y%m%d")
    
    def _initialize_data_paths(self,input_folder_path:str='input', output_folder_path:str='results'):

        intput_folder = Path(input_folder_path)  # 폴더 이름을 지정
        if not intput_folder.exists():
            intput_folder.mkdir(parents=True, exist_ok=True)

        output_folder = Path(output_folder_path)
        if not output_folder.exists():
            output_folder.mkdir(parents=True, exist_ok=True)
        return (intput_folder.resolve(), output_folder.resolve())
            
    
    def _get_holdings(self, url:str, select_q:int, verbose:bool):
        def post_process(df):
            df['% of Portfolio'] = df['% of Portfolio'].str.replace('%', '').replace('', '0').astype(float)
            df['Previous % of Portfolio'] = df['Previous % of Portfolio'].str.replace('%', '').replace('', '0').astype(float)
            df['Shares Held or Principal Amt'] = df['Shares Held or Principal Amt'].str.replace(',', '').astype(float)
            df['Market Value'] = df['Market Value'].str.replace(',', '').astype(float)
            df['Source Date'] = pd.to_datetime(df['Source Date'])
            df['Date Reported'] = pd.to_datetime(df['Date Reported'])
            df['Sector'] = df['Sector'].replace('','None')
            
            df['weight of Portfolio'] = df['Market Value']/df['Market Value'].sum()
            return df
        
        driver = self.web_driver.get_chrome()
        driver.get(url=url)
        self.name = driver.title.split()[0].lower()
        OPERATIING = True
        try:
            
            time.sleep(1)
            holding_tab = driver.find_element(By.XPATH, '//*[@id="app"]/div/main/div/div/div/div[2]/div/div[1]/div/div[2]/div/div[3]')
            ActionChains(driver).move_to_element(holding_tab).click().perform()

            driver.execute_script("arguments[0].scrollIntoView();", holding_tab)
            time.sleep(1)
            
            if verbose:
                driver.save_screenshot(f"{self.name} holdings.png")
            
    
            
            input_tab = driver.find_element(By.XPATH, '//*[@id="app"]/div/main/div/div/div/div[2]/div/div[2]/div/div[2]/section/div/div/div[1]/div[1]/div[1]/div[1]/div/div/div/div[1]/div[2]')
            ActionChains(driver).move_to_element(input_tab).click().perform()
            time.sleep(1)
            if verbose:
                driver.save_screenshot(f"{self.name} input_tab.png")
                
            menu_items = driver.find_elements(By.CSS_SELECTOR, ".v-list-item.v-list-item--link.theme--light")
            if verbose:
                print("드롭다운 메뉴 항목:")
                for idx, item in enumerate(menu_items):
                    print(f"{idx + 1}: {item.text}")
                
            if menu_items:
                title_q = menu_items[select_q].text
                print(f"\n{title_q}")
                menu_items[select_q].click()
                time.sleep(1)
                
            table_df = pd.DataFrame()
            while OPERATIING:

                table_element = driver.find_element(By.XPATH, '//*[@id="app"]/div/main/div/div/div/div[2]/div/div[2]/div/div[2]/section/div/div/div[1]/div[2]/div[2]')
                if verbose:
                    driver.save_screenshot(f"{self.name} table.png")

   
                table_html = table_element.get_attribute('outerHTML')
                time.sleep(1)
                soup = BeautifulSoup(table_html, 'html.parser')
                table = soup.find('table')
                headers = [header.get_text().strip() for header in table.find_all('th')]
                rows = []
                for row in table.find_all('tr')[1:]:  # 첫 번째 tr은 헤더이므로 제외
                    cols = row.find_all('td')
                    cols = [col.get_text().strip() for col in cols]
                    rows.append(cols)
                
                df = pd.DataFrame(rows, columns=headers)
                table_df = pd.concat([table_df, df], axis=0)

                next_button = driver.find_element(By.XPATH, '//*[@id="app"]/div/main/div/div/div/div[2]/div/div[2]/div/div[2]/section/div/div/div[1]/div[2]/div[1]/div[4]')
                next_button.click()
                time.sleep(1)
       
                if verbose:
                    driver.save_screenshot(f"{self.name} next_page.png")

                if table_df.duplicated().any():
                    OPERATIING = False
                    table_df = table_df.drop_duplicates().reset_index(drop=True)
                    table_df = post_process(table_df)
                    
                    
        except Exception as e:
            print(e)
        finally:
            driver.quit()
            return title_q, table_df
            

    def plot_holdings(self):
        df = self.data_df
        sector_shares = df["Sector"].unique()
        colors = px.colors.qualitative.Set3[:len(sector_shares)]  # Set3 팔레트

        # 단일 차트: Current 데이터만 사용
        # category = '% of Portfolio'
        category ='weight of Portfolio'
        # 섹터별 보유 비율 계산
        sector_shares = df.groupby("Sector")[category].sum()  # 섹터별 현재 보유 비율

        # customdata 설정: 섹터별 Stock 이름을 가져옴
        custom_data = df.groupby("Sector")["Stock"].apply(list).loc[sector_shares.index]

        # 파이 차트 생성
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=sector_shares.index,  # 섹터 이름
                    values=sector_shares,        # 각 섹터의 보유 비율
                    hoverinfo="label+percent",   # hover 시 섹터명과 백분율 표시
                    textinfo="label+percent",    # 차트 안에 섹터명과 백분율 표시
                    marker=dict(colors=colors),  # 색상 설정
                    customdata=custom_data,      # customdata에 Stock 이름 추가
                    hovertemplate="%{customdata}"  # Hover 템플릿
                )
            ]
        )

        # 레이아웃 업데이트
        fig.update_layout(
            title="Current Portfolio Distribution",
            template="ggplot2",
            showlegend=False,  # 범례 표시 여부
            width=800,         # 차트 가로 사이즈
            height=800,        # 차트 세로 사이즈
            font=dict(size=9),  # 전체 폰트 크기 설정
            margin=dict(t=50, b=50, l=50, r=50),  # 여백 설정
        )
        
        # 결과 저장 및 표시
        pio.write_html(fig, self.output_folder/f"{self.name}_current_plot_holdings_{self.title_q.split('/')[0]}.html")
        fig.show()
        
        sector_shares.to_excel(self.output_folder/f"{self.name}_current_plot_holdings_{self.title_q.split('/')[0]}.xlsx")
        return sector_shares

    def plot_portfolio_comparasion(self, cut_ratio=.03, y_column = 'Shares Held or Principal Amt'):
        df = self.data_df
        # category ='% of Portfolio'
        category ='weight of Portfolio'
        df = df[df[category] > cut_ratio]  # 특정 비율 이상 데이터만 포함
        
        
        fig = go.Figure()

        # "Current" 데이터만 표시
        fig.add_trace(go.Bar(
            x=df["Stock"], 
            y=df[y_column], 
            name="Current",  # 레전드 이름
            offsetgroup=0,   # 첫 번째 그룹
            hovertemplate="%{y:.1f}%",  # 소수점 1자리까지 표시
            text=(df[y_column]).round(1),  # 소수점 1자리까지 표시
            textposition="outside"  # 텍스트를 바 외부에 표시
        ))

        # 레이아웃 설정
        fig.update_layout(
            title='Current Portfolio(%)',
            template="ggplot2",
            xaxis_title='',
            yaxis_title='',
            barmode='group',  # 바가 나란히 표시됨 (단일 그룹이므로 영향 없음)
            showlegend=True,
            width=1000,       # 차트 가로 사이즈
            height=500,       # 차트 세로 사이즈
            xaxis=dict(
                ticks='', 
            ),
            yaxis=dict(
                showticklabels=False,
                ticks='', 
            ),
            legend=dict(
                orientation='h',  # 레전드를 수평(horizontal)로 배치
                y=1.0,  # 레전드를 차트 위쪽에 배치
                x=0.5,  # 레전드를 차트 중앙에 배치
                xanchor='center',  # x축 기준으로 중앙에 위치하도록 설정
                yanchor='bottom'  # y축 기준으로 위쪽에 위치하도록 설정
            ),
        )

        # 결과 저장 및 표시
        pio.write_html(fig, self.output_folder/f"{self.name}_current_portfolio_{self.title_q.split('/')[0]}.html")
        fig.show()
        df = df.set_index("Stock")
        df = df.loc[:,y_column].astype(int)
        df.to_excel(self.output_folder/f"{self.name}_current_portfolio_{self.title_q.split('/')[0]}.xlsx")
        return 






    # def plot_holdings(self):
    #     df = self.data_df
        # sector_shares = df["Sector"].unique()
        # colors = px.colors.qualitative.Set3[:len(sector_shares)]  # Set3 팔레트

        # # Subplots 설정: 가로로 배치, 두 개의 차트
        # categories = {'Current': '% of Portfolio', 'Previous': 'Previous % of Portfolio'}

        # fig = make_subplots(
        #     rows=1, cols=2,  # rows=1, cols=2로 가로로 배치
        #     subplot_titles=list(categories.keys()),
        #     specs=[[{'type': 'pie'}, {'type': 'pie'}]]  # 각각 파이 차트
        # )

        # for i, (label, category) in enumerate(categories.items(), start=1):
        #     # 섹터별 보유 비율 계산
        #     sector_shares = df.groupby("Sector")[category].sum()  # 섹터별 현재 보유 비율
            
        #     # customdata 설정: 섹터별 Stock 이름을 가져옴
        #     custom_data = df.groupby("Sector")["Stock"].apply(list).loc[sector_shares.index]
            
        #     # 차트 추가
        #     fig.add_trace(
        #         go.Pie(
        #             labels=sector_shares.index,  # 섹터 이름
        #             values=sector_shares,        # 각 섹터의 보유 비율
        #             hoverinfo="label+percent",   # hover 시 섹터명과 백분율 표시
        #             textinfo="label+percent",    # 차트 안에 섹터명과 백분율 표시
        #             marker=dict(colors=colors),  # 색상 설정
        #             customdata=custom_data,      # customdata에 Stock 이름 추가
        #             hovertemplate="%{customdata}",  # Hover 템플릿
        #             name=""  # trace 네임 지정
        #         ), row=1, col=i  # 차트를 가로로 배치
        #     )

        # # 레이아웃 업데이트
        # fig.update_layout(
        #     title="Portfolio Distribution Comparison",
        #     template="ggplot2",
        #     showlegend=False,  # 범례 표시
        #     width=1600,        # 차트 가로 사이즈
        #     height=1200,        # 차트 세로 사이즈
        #     font=dict(size=9),  # 전체 폰트 크기 설정
        #     margin=dict(t=50, b=50, l=50, r=50),  # 여백 설정
        # )

        # pio.write_html(fig, self.output_folder/f"{self.name}_plot_holdings_{self.current_date}.html")
        # fig.show()
    
        
    # def plot_portfolio_comparasion(self, cut_percent=3):
    #     df =self.data_df
    #     df = df[df['% of Portfolio'] > cut_percent]
    #     categories = {'Previous': 'Previous % of Portfolio', 'Current': '% of Portfolio'}
    #     fig = go.Figure()

    #     for i, (label, category) in enumerate(categories.items(), start=0):
    #         fig.add_trace(go.Bar(
    #             x=df["Stock"], 
    #             y=df[category], 
    #             name=label,
    #             offsetgroup=i,  # 첫 번째 그룹
    #             hovertemplate="%{y:.1f}%",  # 소수점 1자리까지 표시
    #             text=df[category].round(1),  # 소수점 1자리까지 표시
    #             textposition="outside"  # 텍스트를 바 외부, 즉 바 위에 표시
    #         ))

    #     # 레이아웃 설정
    #     fig.update_layout(
    #         title='Comparison of Portfolio(%)',
    #         template="ggplot2",
    #         xaxis_title='',
    #         yaxis_title='',
    #         barmode='group',  # 바가 나란히 표시됨
    #         showlegend=True,
    #         width=1000,       # 차트 가로 사이즈
    #         height=500,       # 차트 세로 사이즈
    #         xaxis=dict(
    #             ticks='', 
    #         ),
    #         yaxis=dict(
    #             showticklabels=False,
    #             ticks='', 
    #         ),
    #             legend=dict(
    #             orientation='h',  # 레전드를 수평(horizontal)로 배치
    #             y=1.0,  # 레전드를 차트 위쪽으로 배치
    #             x=0.5,  # 레전드를 차트 중앙에 배치
    #             xanchor='center',  # x축 기준으로 중앙에 위치하도록 설정
    #             yanchor='bottom'  # y축 기준으로 위쪽에 위치하도록 설정
    #         ),

    #     )
    #     pio.write_html(fig, self.output_folder/f"{self.name}_plot_portfolio_comparasion_{self.current_date}.html")
    #     fig.show()
        