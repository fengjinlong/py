import requests
import pandas as pd
import talib
import time

# 获取历史价格数据
def fetch_price_data(coin_id, days=30):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        prices = data['prices']
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    else:
        print(f"获取价格数据失败: {response.status_code}")
        return None

# 获取基础面数据
def fetch_fundamentals(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        market_cap = data['market_data']['market_cap']['usd']
        volume = data['market_data']['total_volume']['usd']
        return market_cap, volume
    else:
        print(f"获取基础数据失败: {response.status_code}")
        return None, None

# 计算技术指标
def calculate_indicators(df):
    df['RSI'] = talib.RSI(df['price'], timeperiod=14)
    df['SMA20'] = talib.SMA(df['price'], timeperiod=20)
    df['SMA50'] = talib.SMA(df['price'], timeperiod=50)
    return df

# 确定入场、观望、平仓点位
def determine_positions(df, market_cap, volume):
    latest_rsi = df['RSI'].iloc[-1]
    latest_sma20 = df['SMA20'].iloc[-1]
    latest_sma50 = df['SMA50'].iloc[-1]
    
    # 技术面规则
    if latest_rsi < 30 and latest_sma20 > latest_sma50:
        tech_signal = "入场"
    elif latest_rsi > 70 or latest_sma20 < latest_sma50:
        tech_signal = "平仓"
    else:
        tech_signal = "观望"
    
    # 基础面规则
    if market_cap > 1e9 and volume > 1e8:
        fund_signal = "积极"
    else:
        fund_signal = "谨慎"
    
    return tech_signal, fund_signal

# 主函数
def main():
    # coin_id = "curve-dao-token"
    coin_id = "bitcoin"
    while True:
        df = fetch_price_data(coin_id)
        if df is not None:
            df = calculate_indicators(df)
            market_cap, volume = fetch_fundamentals(coin_id)
            if market_cap is not None:
                tech_signal, fund_signal = determine_positions(df, market_cap, volume)
                current_price = df['price'].iloc[-1]
                current_rsi = df['RSI'].iloc[-1]
                current_sma20 = df['SMA20'].iloc[-1]
                current_sma50 = df['SMA50'].iloc[-1]
                
                print(f"时间: {pd.Timestamp.now()}")
                print(f"币种: {coin_id}")
                print(f"当前价格: ${current_price:.4f}")
                print(f"RSI(14): {current_rsi:.2f}")
                print(f"20日均线: ${current_sma20:.4f}")
                print(f"50日均线: ${current_sma50:.4f}")
                print(f"技术面建议: {tech_signal}")
                print(f"基础面信号: {fund_signal}")
                print("-" * 50)
        time.sleep(3600)  # 每小时运行一次

if __name__ == "__main__":
    main()