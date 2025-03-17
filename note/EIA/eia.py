import requests
import pandas as pd

def json_to_dataframe(func):
    """
    API에서 받은 JSON 데이터를 pandas DataFrame으로 변환하는 데코레이터
    """
    def wrapper(self, *args, **kwargs):
        data = func(self, *args, **kwargs)
        if data and "response" in data and "data" in data["response"]:
            # JSON에서 'response' -> 'data' 항목을 가져와 DataFrame으로 변환
            return pd.DataFrame(data["response"]["data"])
        return None  # 만약 데이터가 없다면 None 반환
    return wrapper


class EIA:
    def __init__(self, api_key):
        self.api_key = api_key
        
    @json_to_dataframe  
    def _get_data(self, url, frequency="annual", data_type="value", start_year=None, end_year=None, sort_column="period", sort_direction="desc", offset=0, length=5000):
        params = {
            "frequency": frequency,
            "data[0]": data_type,
            "start": start_year,
            "end": end_year,
            "sort[0][column]": sort_column,
            "sort[0][direction]": sort_direction,
            "offset": offset,
            "length": length,
            "api_key": self.api_key
        }

        response = requests.get(url, params=params)  # 수정된 부분

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            return None


class NATURALGAS(EIA):
    def __init__(self, api_key):  # api_key를 받도록 수정
        super().__init__(api_key)  # super()를 사용하여 부모 클래스 초기화
            
    def get_number_of_producing_gas_wells(self, frequency="annual", start_year="2002", end_year="2024"):
        url = "https://api.eia.gov/v2/natural-gas/prod/wells/data/"
        return self._get_data(url, frequency, start_year=start_year, end_year=end_year)

    def get_shale_gas_production(self, frequency="annual", start_year="2002", end_year="2024"):
        url = "https://api.eia.gov/v2/natural-gas/prod/shalegas/data/"
        return self._get_data(url, frequency, start_year=start_year, end_year=end_year)
        
    def get_natural_gas_import_move(self, frequency="monthly", start_year="2002-02", end_year="2024-03"):
        url = "https://api.eia.gov/v2/natural-gas/move/impc/data"
        return self._get_data(url, frequency, start_year=start_year, end_year=end_year)

    def get_natual_gas_price(self, frequency="monthly", start_year="2002-02", end_year="2024-03"):
        url = "https://api.eia.gov/v2/natural-gas/pri/sum/data/"
        return self._get_data(url, frequency, start_year=start_year, end_year=end_year)
    
    def get_natual_gas_price_for_cunsumer(self, frequency="monthly", start_year="2002-02", end_year="2024-03"):
        url = "https://api.eia.gov/v2/natural-gas/pri/rescom/data/"
        return self._get_data(url, frequency, start_year=start_year, end_year=end_year)




class TOTALENERGY(EIA):
    def __init__(self, api_key):  # api_key를 받도록 수정
        super().__init__(api_key)  # super()를 사용하여 부모 클래스 초기화
        
    def get_total_energy(self, frequency="monthly", start_year="2002", end_year="2024"):
        url = "https://api.eia.gov/v2/total-energy/data/"
        return self._get_data(url, frequency, start_year=start_year, end_year=end_year)
        
class STEO(EIA):
    def __init__(self, api_key):  
        super().__init__(api_key) 
        
    def get_steo_data(self, frequency="monthly", start_year="2007-01", end_year="2024-11"):
        url = "https://api.eia.gov/v2/steo/data/"
        return self._get_data(url, frequency, start_year=start_year, end_year=end_year)
        
class CRUDE(EIA):
    def __init__(self, api_key):  
        super().__init__(api_key)  
        
    def get_crude_oil_import(self, frequency="monthly", start_year="2007-01", end_year="2024-11"):
        """
        montly, annual
        """
        url = "https://api.eia.gov/v2/crude-oil-imports/data"
        return self._get_data(url, frequency, start_year=start_year, end_year=end_year)


class NUCLEAR(EIA):
    def __init__(self, api_key):  
        super().__init__(api_key) 

    def get_nuclear_outages(self, frequency="daily", data_type=["capacity"], start_year="2007-01", end_year="2024-11"):
        """
        원자력 발전소 정지 데이터 가져오기
        frequency: 데이터 주기 (daily, monthly 등)
        data_type: 가져올 데이터 항목 (capacity, outage, percentOutage)
        """
        url = "https://api.eia.gov/v2/nuclear-outages/us-nuclear-outages/data/"  # 올바른 URL로 수정
        return self._get_data(url, frequency, data_type, start_year=start_year, end_year=end_year)
