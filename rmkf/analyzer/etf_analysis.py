import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

class ETFAnalysis:
    def __init__(self, data_store_path):
        self.data_store_path = data_store_path
        self.base_ticker = None
        self.start_date = None
        self.etf_ticker = None
        self.etf_prices = None
        self.monthly_prices = None
        self.risk_free = None
        self.etf_corr_with_baseetf = None
        self.df_corr = pd.DataFrame()
        self.df_rtn = pd.DataFrame()
    

    def set_etf(self, base_ticker, start_date):
        self.base_ticker = base_ticker
        self.start_date = start_date
    
        self._load_etf_data()
        self._load_riskfree_data(year='10')
        self._clean_data()
        self._calculate_monthly_returns()
        self._load_risk_free_rate()
        self._calculate_corr_distribution()
        self._plot_corr_distribution()
        self._calculate_performance()
        
        for i in range(len(self.df_rtn.index)):
            setattr(
                self, 
                f"get_top_etfs_idx{i}", 
                lambda top_n=5, i=i: self._print_and_get_etfs(i, top_n)
            )
        

            
    def _load_etf_data(self):
        # ETF 정보 로딩
        with pd.HDFStore(self.data_store_path, mode='r') as store:
            key = f'us/etfs/symbols/etfdb'
            self.etf_ticker = store[key]
        
        # ETF 가격 로딩
        with pd.HDFStore(self.data_store_path, mode='r') as store:
            key = f'us/etfs/prices/yfinance'
            etf = store[key]
        etf = etf[~etf.index.duplicated()]
        self.etf_prices = etf['close'].unstack('symbol')

    def _load_riskfree_data(self, year='10'):
        # risk_free rate  로딩
        with pd.HDFStore(self.data_store_path, mode='r') as store:
            key = f'us/fund_rate/prices/fred'
            data = store[key]
        data.columns = data.columns.str.lower()
        risk_free = data.filter(like='treasury').filter(like=year).dropna()    
        risk_free = risk_free.droplevel('symbol')
        risk_free.index = pd.to_datetime(risk_free.index)
        self.risk_free = risk_free
 


    
    def _clean_data(self):
        def clean_string(value):
            if isinstance(value, str):
                if value.upper() == 'N/A':  # 'N/A' 처리
                    return np.nan
                value = value.replace('$', '').replace(',', '').replace('%', '')
                try:
                    return float(value)  # 숫자로 변환
                except ValueError:
                    return np.nan  # 변환 실패 시 NaN 반환
            return value

        # ETF 데이터 정리
        self.etf_ticker['total assets ($mm)'] = self.etf_ticker['total assets ($mm)'].apply(clean_string)
        self.etf_ticker['total assets ($mm)'] = self.etf_ticker['total assets ($mm)'].fillna(0).astype(float).astype(int)
        self.etf_ticker['ytd price change(%)'] = (self.etf_ticker['ytd price change'].apply(clean_string).astype(float) / 100)
        self.etf_ticker['avg. daily share volume (3mo)'] = self.etf_ticker['avg. daily share volume (3mo)'].apply(clean_string)
        self.etf_ticker['avg. daily share volume (3mo)'] = self.etf_ticker['avg. daily share volume (3mo)'].fillna(0).astype(float).astype(int)
        self.etf_ticker['previous closing price($)'] = self.etf_ticker['previous closing price'].apply(clean_string).astype(float)
        self.etf_ticker = self.etf_ticker.drop(['previous closing price', 'ytd price change', 'etf database pro', 'watchlist'], axis=1)


    def _calculate_monthly_returns(self):
        prices = self.etf_prices[self.start_date:].dropna(axis=1)
        prices.index = prices.index.map(lambda x: pd.to_datetime(x))
        self.monthly_prices = prices.resample('ME').last()
        base_etf = self.monthly_prices.pct_change()[self.base_ticker]
        self.etf_corr_with_baseetf = self.monthly_prices.pct_change().corrwith(base_etf).sort_values(ascending=False)

    def _load_risk_free_rate(self):
        start_date = self.monthly_prices.index[0]
        end_date = self.monthly_prices.index[-1]
        self.risk_free = self.risk_free[start_date:end_date].resample('ME').last() / 100  # 무위험 수익률

    def _calculate_corr_distribution(self, step=2):
        def filter_corr(df, lower, upper):
            ds = df[(lower < df) & (df <= upper)]
            ds.name = f'({lower}, {upper}]'
            return ds

        # 상관관계 구간 계산
        for i in range(-10, 10, step):
            lower = i / 10
            upper = (i + step) / 10
            filtered_series = filter_corr(self.etf_corr_with_baseetf, lower, upper)
            self.df_corr = pd.concat([self.df_corr, filtered_series], axis=1)


    def _calculate_performance(self):
        # 성과 계산
        for idx in self.df_corr.columns:
            tickers = self.df_corr[idx].dropna().index
            cum_rtn = (
                self.monthly_prices[tickers].pct_change()
                .add(1)
                .cumprod()
                .dropna()
                .tail(1)
                .mean(axis=1)
                .squeeze()
            )
            try:
                mean_std = (
                    self.monthly_prices[tickers].pct_change().dropna().std(axis=1)
                    .mean()
                    .squeeze()
                )
            except:
                mean_std = np.nan

            mean_sharpe = (
                (
                    self.monthly_prices[tickers].pct_change().dropna().mean(axis=1)
                    / self.monthly_prices[tickers].pct_change().dropna().std(axis=1)
                ) - self.risk_free.squeeze()
            ).mean()

            mean_std_df = pd.DataFrame({
                'rtn_cum': [cum_rtn],
                'std': [mean_std],
                'sharpe': [mean_sharpe],
            }, index=[idx])

            self.df_rtn = pd.concat([self.df_rtn, mean_std_df])

    def _sort_by_sharpe_ratio(self):
        self.df_rtn.index.name = 'correlation'
        return self.df_rtn.sort_values(by=['sharpe'], ascending=False)
    
    def _plot_corr_distribution(self):
        # 상관관계 분포 히스토그램
        print(f"{self.base_ticker}와의 상관관계 분포 (ETF 개수 기준)")
        sns.histplot(self.df_corr, palette='tab10')
        plt.show()
        
    def _get_top_etfs(self, idx=0, top_n=5):
        # 샤프 비율이 가장 높은 상관관계 그룹의 ETF 정보
        idx = self.df_rtn.sort_values(by=['sharpe'], ascending=False).index[idx]
        tickers = self.df_corr[idx].dropna().index
        return self.etf_ticker.loc[list(tickers), :] \
            .sort_values(by=['total assets ($mm)', 'avg. daily share volume (3mo)', 'ytd price change(%)'], ascending=False) \
            .head(top_n)


    def _print_and_get_etfs(self, idx, top_n):
        corr_range = self.df_rtn.index[idx].split(',')
        corr_lower= corr_range[0].replace('(','').strip()
        corr_upper= corr_range[1].replace(']','').strip()
        print(f"{self.base_ticker}와 {corr_lower} ~ {corr_upper} 사이의 상관관계를 가진 ETF 목록:")
        return self._get_top_etfs(idx=idx, top_n=top_n)
        
