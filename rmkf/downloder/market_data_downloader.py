import pandas as pd
import yfinance as yf
import FinanceDataReader as fdr
import pandas_datareader.data as web
from tqdm import tqdm
import time
from datetime import datetime

class MarketDataDownloader:
    def __init__(self, start_date:str= None, end_date:str=None) -> None:
        
        if start_date is None:
            self.start_date = "2000-01-01"
        else:
            self.start_date = start_date
        
        if end_date is None:
            self.end_date = datetime.today().strftime('%Y-%m-%d')
        else:
            self.end_date = end_date
        
    
    def download_prices(self, symbols:list, src:str=None)-> pd.DataFrame:
        prices_list = []
        if not isinstance(symbols, list):
            try: 
                symbols = list(symbols)
            except:
                raise ValueError
            
        for symbol in tqdm(symbols):
            try:
                if src:
                    price_info = fdr.DataReader(f'{src}:{symbol}', start=self.start_date, end=self.end_date)   
                else:    
                    price_info = fdr.DataReader(symbol, start=self.start_date, end=self.end_date)
                    
                price_info = price_info.reset_index()
                price_info.columns = price_info.columns.str.lower()
                price_info = price_info.rename(columns={'index': 'date'})
                price_info['date'] = pd.to_datetime(price_info['date'])
                price_info = price_info.set_index('date')
                if 'adj close' in price_info.columns:
                    multiple = price_info['adj close'] / price_info['close']
                    multiple_2d = multiple.values.reshape(-1, 1) 
                    price_info[['open', 'high', 'low', 'close']] = price_info[['open', 'high', 'low', 'close']].multiply(multiple_2d, axis=0)  # 가격 조정정
            except Exception as e:
                print(f"{symbol}: {e}")
                continue

            time.sleep(1)

            price_info['symbol'] = symbol
            prices_list.append(price_info)
        prices_df = pd.concat(prices_list)
        return prices_df
    
    def remake_df(self, prices_df:pd.DataFrame) -> pd.DataFrame:
        # 날짜 형식으로 인덱스 변환 시도
        if pd.api.types.is_datetime64_any_dtype(prices_df.index):
            prices_df.index = prices_df.index.strftime('%Y-%m-%d')
        
        # 불필요한 컬럼 제거
        columns_to_drop = ['adj close', 'capital gains', 'stock splits']
        for column in columns_to_drop:
            if column in prices_df.columns:
                prices_df = prices_df.drop([column], axis=1)
        
        # 인덱스 재설정 및 컬럼명 정리
        prices_df = prices_df.reset_index()
        prices_df.columns = prices_df.columns.str.lower()
        prices_df.columns = prices_df.columns.str.replace("dividends", "dividend")
        
        # 인덱스 설정 및 중복 제거
        if 'symbol' in prices_df.columns and 'date' in prices_df.columns:
            prices_df = prices_df.set_index(['symbol', 'date'])
            prices_df = prices_df[~prices_df.index.duplicated(keep='first')]
        
        return prices_df

    def df_intersection(self, single_index_df: pd.DataFrame, multi_index_df: pd.DataFrame, multi_idx:str='symbol') -> tuple[pd.DataFrame, pd.DataFrame]:

        prices_tickers = multi_index_df.index.get_level_values(multi_idx).unique()

        symbols_tickers = single_index_df.index.unique()
        
        common_tickers = set(prices_tickers).intersection(symbols_tickers)
        
        filtered_prices_df = multi_index_df[multi_index_df.index.get_level_values(multi_idx).isin(common_tickers)]
        filtered_symbols_df = single_index_df[single_index_df.index.isin(common_tickers)]
        
        return filtered_symbols_df, filtered_prices_df




# import pandas as pd
# import yfinance as yf
# import FinanceDataReader as fdr
# import pandas_datareader.data as web
# from tqdm import tqdm
# import time
# from datetime import datetime

# class MarketDataDownloader:
#     def __init__(self, start_date:str= None, end_date:str=None) -> None:
        
#         if start_date is None:
#             self.start_date = "2000-01-01"
#         else:
#             self.start_date = start_date
        
#         if end_date is None:
#             self.end_date = datetime.today().strftime('%Y-%m-%d')
#         else:
#             self.end_date = end_date
        
    
#     def download_prices(self, symbols:list, src:str='yfinance')-> pd.DataFrame:
#         prices_list = []
#         src_prefix = src.split(':')[-1]
#         src = src.split(':')[0]
#         if not isinstance(symbols, list):
#             try: 
#                 symbols = list(symbols)
#             except:
#                 raise ValueError
            
#         for ticker in tqdm(symbols):
#             if src == 'yfinance':
#                 stock = yf.Ticker(ticker)
#                 price_info = stock.history(start=self.start_date, end=self.end_date)
                
#             elif src == 'fdr':
#                 try:
#                     if src_prefix:
#                         price_info = fdr.DataReader(f'{src_prefix}:{ticker}', start=self.start_date, end=self.end_date)   
#                     else:    
#                         price_info = fdr.DataReader(ticker, start=self.start_date, end=self.end_date)
                        
#                     price_info = price_info.reset_index()
#                     price_info.columns = price_info.columns.str.lower()
#                     price_info = price_info.rename(columns={'index': 'date'})
#                     price_info['date'] = pd.to_datetime(price_info['date'])
#                     price_info = price_info.set_index('date')
#                     if 'adj close' in price_info.columns:
#                         multiple = price_info['adj close'] / price_info['close']
#                         multiple_2d = multiple.values.reshape(-1, 1)  # (59722, 1) 형태로 변환
#                         price_info[['open', 'high', 'low', 'close']] = price_info[['open', 'high', 'low', 'close']].multiply(multiple_2d, axis=0)  # 가격 조정정
#                 except Exception as e:
#                     print(f"{ticker}: {e}")
#                     continue
#             elif src == 'fred':
#                 price_info = web.DataReader(ticker, "fred", start=self.start_date, end=self.end_date)
            
#             time.sleep(1)

#             price_info['ticker'] = ticker
#             prices_list.append(price_info)
#         prices_df = pd.concat(prices_list)
#         return prices_df
    
#     def remake_df(self, prices_df:pd.DataFrame) -> pd.DataFrame:
#         # 날짜 형식으로 인덱스 변환 시도
#         if pd.api.types.is_datetime64_any_dtype(prices_df.index):
#             prices_df.index = prices_df.index.strftime('%Y-%m-%d')
        
#         # 불필요한 컬럼 제거
#         columns_to_drop = ['adj close', 'capital gains', 'stock splits']
#         for column in columns_to_drop:
#             if column in prices_df.columns:
#                 prices_df = prices_df.drop([column], axis=1)
        
#         # 인덱스 재설정 및 컬럼명 정리
#         prices_df = prices_df.reset_index()
#         prices_df.columns = prices_df.columns.str.lower()
#         prices_df.columns = prices_df.columns.str.replace("dividends", "dividend")
        
#         # 인덱스 설정 및 중복 제거
#         if 'ticker' in prices_df.columns and 'date' in prices_df.columns:
#             prices_df = prices_df.set_index(['ticker', 'date'])
#             prices_df = prices_df[~prices_df.index.duplicated(keep='first')]
        
#         return prices_df

#     def df_intersection(self, single_index_df: pd.DataFrame, multi_index_df: pd.DataFrame, multi_idx:str='ticker') -> tuple[pd.DataFrame, pd.DataFrame]:

#         prices_tickers = multi_index_df.index.get_level_values(multi_idx).unique()

#         symbols_tickers = single_index_df.index.unique()
        
#         common_tickers = set(prices_tickers).intersection(symbols_tickers)
        
#         filtered_prices_df = multi_index_df[multi_index_df.index.get_level_values(multi_idx).isin(common_tickers)]
#         filtered_symbols_df = single_index_df[single_index_df.index.isin(common_tickers)]
        
#         return filtered_symbols_df, filtered_prices_df
