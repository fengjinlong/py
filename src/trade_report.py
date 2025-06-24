import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import numpy as np
from trade2 import fetch_price_data, fetch_fundamentals, calculate_indicators, determine_positions

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        return super().default(obj)

def create_candlestick_chart(df):
    # 创建子图
    fig = make_subplots(rows=3, cols=1, 
                       shared_xaxes=True,
                       vertical_spacing=0.05,
                       row_heights=[0.6, 0.2, 0.2])

    # 添加K线图
    fig.add_trace(go.Candlestick(
        x=df['timestamp'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='OHLC'
    ), row=1, col=1)

    # 添加均线
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['SMA20'],
        name='SMA20',
        line=dict(color='orange')
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['SMA50'],
        name='SMA50',
        line=dict(color='blue')
    ), row=1, col=1)

    # 添加成交量图
    fig.add_trace(go.Bar(
        x=df['timestamp'],
        y=df['volume'],
        name='Volume'
    ), row=2, col=1)

    # 添加RSI图
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['RSI'],
        name='RSI'
    ), row=3, col=1)

    # 添加RSI的超买超卖线
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    # 更新布局
    fig.update_layout(
        title='Trading Analysis Dashboard',
        yaxis_title='Price (USD)',
        yaxis2_title='Volume',
        yaxis3_title='RSI',
        xaxis_rangeslider_visible=False
    )

    return fig

def generate_html_report(coin_id="bitcoin"):
    # 获取数据
    df = fetch_price_data(coin_id)
    if df is not None:
        df = calculate_indicators(df)
        market_cap, volume = fetch_fundamentals(coin_id)
        
        if market_cap is not None:
            tech_signal, fund_signal, divergence, buy_signals, sell_signals = determine_positions(df, market_cap, volume)
            
            # 创建图表
            fig = create_candlestick_chart(df)
            
            # 生成HTML报告
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Trading Analysis Report</title>
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .container {{ max-width: 1200px; margin: 0 auto; }}
                    .metrics {{ 
                        display: grid; 
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 20px;
                        margin: 20px 0;
                    }}
                    .metric-card {{
                        background: #f5f5f5;
                        padding: 15px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .signal {{
                        font-weight: bold;
                        color: #1a73e8;
                    }}
                    .divergence {{
                        font-weight: bold;
                        color: {{'#e53935' if '看跌' in divergence else '#43a047' if '看涨' in divergence else '#757575'}};
                    }}
                    .buy-signals {{
                        color: #43a047;
                        font-weight: bold;
                    }}
                    .sell-signals {{
                        color: #e53935;
                        font-weight: bold;
                    }}
                    .no-signals {{
                        color: #757575;
                        font-style: italic;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Trading Analysis Report - {coin_id.upper()}</h1>
                    <div class="metrics">
                        <div class="metric-card">
                            <h3>Current Price</h3>
                            <p>${float(df['close'].iloc[-1]):.2f}</p>
                        </div>
                        <div class="metric-card">
                            <h3>24h Volume</h3>
                            <p>${float(volume):,.2f}</p>
                        </div>
                        <div class="metric-card">
                            <h3>Market Cap</h3>
                            <p>${float(market_cap):,.2f}</p>
                        </div>
                        <div class="metric-card">
                            <h3>RSI (14)</h3>
                            <p>{float(df['RSI'].iloc[-1]):.2f}</p>
                        </div>
                        <div class="metric-card">
                            <h3>Buy Signals</h3>
                            <p class="{'buy-signals' if buy_signals else 'no-signals'}">
                                {', '.join(buy_signals) if buy_signals else 'No buy signals'}
                            </p>
                        </div>
                        <div class="metric-card">
                            <h3>Sell Signals</h3>
                            <p class="{'sell-signals' if sell_signals else 'no-signals'}">
                                {', '.join(sell_signals) if sell_signals else 'No sell signals'}
                            </p>
                        </div>
                        <div class="metric-card">
                            <h3>Technical Signal</h3>
                            <p class="signal">{tech_signal}</p>
                        </div>
                        <div class="metric-card">
                            <h3>Fundamental Signal</h3>
                            <p class="signal">{fund_signal}</p>
                        </div>
                        <div class="metric-card">
                            <h3>OBV Divergence</h3>
                            <p class="divergence">{divergence}</p>
                        </div>
                    </div>
                    <div id="chart"></div>
                    <script>
                        var graphs = {json.dumps(fig.to_dict(), cls=NumpyEncoder)};
                        Plotly.newPlot('chart', graphs.data, graphs.layout);
                    </script>
                </div>
            </body>
            </html>
            """
            
            # 保存HTML文件
            with open(f"{coin_id}_report.html", "w") as f:
                f.write(html_content)
            
            print(f"Report generated: {coin_id}_report.html")
            return True
    return False

if __name__ == "__main__":
    generate_html_report() 