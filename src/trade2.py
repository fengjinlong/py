import requests
import pandas as pd
import talib
import time
from scipy.signal import find_peaks

# 获取 OHLC 和成交量数据
def fetch_price_data(coin_id, days=30):
    # 获取 OHLC 数据
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc?vs_currency=usd&days={days}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # 检查 HTTP 错误
        data = response.json()
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # 计算真实波幅（TR）
        df['TR'] = pd.DataFrame({
            'hl': df['high'] - df['low'],
            'hc': abs(df['high'] - df['close'].shift(1)),
            'lc': abs(df['low'] - df['close'].shift(1))
        }).max(axis=1)
        
        # 计算平均真实波幅（ATR）
        df['ATR'] = df['TR'].rolling(window=14).mean()
        
        # 获取成交量数据
        url_volume = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
        response_volume = requests.get(url_volume)
        response_volume.raise_for_status()
        volume_data = response_volume.json()['total_volumes']
        
        # 处理成交量数据
        if len(volume_data) >= len(df):
            df['volume'] = [vol[1] for vol in volume_data[:len(df)]]
        else:
            volumes = [vol[1] for vol in volume_data]
            volumes.extend([0] * (len(df) - len(volumes)))
            df['volume'] = volumes
        
        # 添加蜡烛图模式识别
        df['body'] = df['close'] - df['open']
        df['upper_shadow'] = df.apply(lambda x: x['high'] - max(x['open'], x['close']), axis=1)
        df['lower_shadow'] = df.apply(lambda x: min(x['open'], x['close']) - x['low'], axis=1)
        
        print(f"数据形状: {df.shape}")
        print(f"列名: {df.columns.tolist()}")
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"API 请求失败: {e}")
        return None
    except Exception as e:
        print(f"处理数据时出错: {e}")
        return None

# 获取基础面数据
def fetch_fundamentals(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false"
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
    df['RSI'] = talib.RSI(df['close'], timeperiod=14)
    df['SMA20'] = talib.SMA(df['close'], timeperiod=20)
    df['SMA50'] = talib.SMA(df['close'], timeperiod=50)
    df['upper_band'], df['middle_band'], df['lower_band'] = talib.BBANDS(df['close'], timeperiod=20, nbdevup=2, nbdevdn=2)
    df['OBV'] = talib.OBV(df['close'], df['volume'])
    df['slowk'], df['slowd'] = talib.STOCH(df['high'], df['low'], df['close'], fastk_period=14, slowk_period=3, slowd_period=3)
    df['CCI'] = talib.CCI(df['high'], df['low'], df['close'], timeperiod=20)
    df['macd'], df['signal'], df['hist'] = talib.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    df['ADX'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
    return df

# 检测 OBV 背离
def detect_obv_divergence(df, window=5):
    price_peaks, _ = find_peaks(df['close'], distance=window)
    price_troughs, _ = find_peaks(-df['close'], distance=window)
    obv_peaks, _ = find_peaks(df['OBV'], distance=window)
    obv_troughs, _ = find_peaks(-df['OBV'], distance=window)
    
    price_peaks = price_peaks[-2:] if len(price_peaks) >= 2 else []
    obv_peaks = obv_peaks[-2:] if len(obv_peaks) >= 2 else []
    price_troughs = price_troughs[-2:] if len(price_troughs) >= 2 else []
    obv_troughs = obv_troughs[-2:] if len(obv_troughs) >= 2 else []
    
    divergence = "无背离"
    
    if len(price_peaks) == 2 and len(obv_peaks) == 2:
        if (df['close'].iloc[price_peaks[-1]] > df['close'].iloc[price_peaks[-2]] and
            df['OBV'].iloc[obv_peaks[-1]] < df['OBV'].iloc[obv_peaks[-2]]):
            divergence = "看跌背离"
    
    if len(price_troughs) == 2 and len(obv_troughs) == 2:
        if (df['close'].iloc[price_troughs[-1]] < df['close'].iloc[price_troughs[-2]] and
            df['OBV'].iloc[obv_troughs[-1]] > df['OBV'].iloc[obv_troughs[-2]]):
            divergence = "看涨背离"
    
    return divergence

# 检测各指标的买入和卖出信号
def stochastic_buy(df):
    return (df['slowk'].iloc[-1] > df['slowd'].iloc[-1] and 
            df['slowk'].iloc[-2] < df['slowd'].iloc[-2] and 
            df['slowk'].iloc[-1] < 20)

def stochastic_sell(df):
    return (df['slowk'].iloc[-1] < df['slowd'].iloc[-1] and 
            df['slowk'].iloc[-2] > df['slowd'].iloc[-2] and 
            df['slowk'].iloc[-1] > 80)

def macd_buy(df):
    return (df['macd'].iloc[-1] > df['signal'].iloc[-1] and 
            df['macd'].iloc[-2] < df['signal'].iloc[-2])

def macd_sell(df):
    return (df['macd'].iloc[-1] < df['signal'].iloc[-1] and 
            df['macd'].iloc[-2] > df['signal'].iloc[-2])

def cci_buy(df):
    return df['CCI'].iloc[-1] < -100

def cci_sell(df):
    return df['CCI'].iloc[-1] > 100

# 确定交易点位
def determine_positions(df, market_cap, volume):
    latest_rsi = df['RSI'].iloc[-1]
    latest_sma20 = df['SMA20'].iloc[-1]
    latest_sma50 = df['SMA50'].iloc[-1]
    latest_price = df['close'].iloc[-1]
    latest_upper = df['upper_band'].iloc[-1]
    latest_lower = df['lower_band'].iloc[-1]
    latest_adx = df['ADX'].iloc[-1]
    divergence = detect_obv_divergence(df)
    
    buy_signals = []
    if stochastic_buy(df):
        buy_signals.append("Stochastic")
    if macd_buy(df):
        buy_signals.append("MACD")
    if cci_buy(df):
        buy_signals.append("CCI")
    if latest_rsi < 30 and latest_sma20 > latest_sma50 and latest_price < latest_lower:
        buy_signals.append("RSI+BB")
    
    sell_signals = []
    if stochastic_sell(df):
        sell_signals.append("Stochastic")
    if macd_sell(df):
        sell_signals.append("MACD")
    if cci_sell(df):
        sell_signals.append("CCI")
    if latest_rsi > 70 or latest_sma20 < latest_sma50 or latest_price > latest_upper:
        sell_signals.append("RSI+BB")
    
    tech_signal = "观望"
    if len(buy_signals) >= 2 and latest_adx > 25 and divergence != "看跌背离":
        tech_signal = "入场"
    elif len(sell_signals) >= 2 and latest_adx > 25 and divergence != "看涨背离":
        tech_signal = "平仓"
    elif divergence == "看涨背离":
        tech_signal = "入场"
    elif divergence == "看跌背离":
        tech_signal = "平仓"
    
    fund_signal = "谨慎"
    if market_cap > 1e9 and volume > 1e8:
        fund_signal = "积极"
    
    return tech_signal, fund_signal, divergence, buy_signals, sell_signals

# 主函数
def main():
    coin_id = "bitcoin"
    # coin_id = "curve-dao-token"
    while True:
        df = fetch_price_data(coin_id)
        if df is not None:
            df = calculate_indicators(df)
            market_cap, volume = fetch_fundamentals(coin_id)
            if market_cap is not None:
                tech_signal, fund_signal, divergence, buy_signals, sell_signals = determine_positions(df, market_cap, volume)
                
                # 打印基本信息
                print(f"\n{'='*60}")
                print(f"时间: {pd.Timestamp.now()}")
                print(f"币种: {coin_id}")
                print(f"当前价格: {df['close'].iloc[-1]:.2f} USD")
                print(f"{'='*60}\n")
                
                # 打印技术指标
                print("技术指标:")
                print(f"布林带: 上轨={df['upper_band'].iloc[-1]:.2f}, 中轨={df['middle_band'].iloc[-1]:.2f}, 下轨={df['lower_band'].iloc[-1]:.2f}")
                print(f"OBV: {df['OBV'].iloc[-1]:.0f}")
                print(f"OBV背离: {divergence}")
                print(f"Stochastic: %K={df['slowk'].iloc[-1]:.2f}, %D={df['slowd'].iloc[-1]:.2f}")
                print(f"CCI: {df['CCI'].iloc[-1]:.2f}")
                print(f"MACD: MACD={df['macd'].iloc[-1]:.2f}, 信号线={df['signal'].iloc[-1]:.2f}")
                print(f"ADX: {df['ADX'].iloc[-1]:.2f}\n")
                
                # 打印信号分析
                print("信号分析:")
                print(f"买入信号: {', '.join(buy_signals) if buy_signals else '无'}")
                print(f"卖出信号: {', '.join(sell_signals) if sell_signals else '无'}")
                print(f"技术面建议: {tech_signal}")
                print(f"基础面信号: {fund_signal}")
                print(f"\n{'-'*60}")
                
        time.sleep(3600)  # 每10分钟运行一次

if __name__ == "__main__":
    main()