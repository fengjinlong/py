import feedparser
import pandas as pd
import datetime
import requests
import newspaper  # ★ 1. 导入 newspaper3k
from time import time
import concurrent.futures
import sys
import calendar
from zhipuai import ZhipuAI  # 导入 智谱AI
from tqdm import tqdm

# (newspaper3k 会自动处理 lxml，这里不再需要)

# ====== 配置区域 ======
# ！！！注意：请务必替换为你自己的 KEY！！！
# 从 智谱AI 开放平台 (open.bigmodel.cn) 获取
ZHIPU_API_KEY = "06314b501e4a4135b1989d56c32a2324.495r1QkUVZQmWD0W"  # ←←← 替换成你的 Key
if "YOUR_ZHIPU_API_KEY_HERE" in ZHIPU_API_KEY:
    print("错误：请在脚本中设置你的 ZHIPU_API_KEY。", file=sys.stderr)
    sys.exit(1)
    
# ★ 配置 智谱AI 客户端
client = ZhipuAI(api_key=ZHIPU_API_KEY)

RSS_FEEDS = {
    'c1': 'https://www.coindesk.com/arc/outboundfeeds/rss',
    'c2': 'https://cointelegraph.com/rss/category/op-ed',
    'c3': 'https://cointelegraph.com/rss/category/hodlers-digest',
    'c4': 'https://cointelegraph.com/rss/category/markets',
    'c6': 'https://thedefiant.io/feed/',
    'c7': 'https://cryptonews.com/news/feed',
    'c9': 'https://coinjournal.net/news/feed',
    "Decrypt": "https://decrypt.co/feed",
    # "CryptoSlate": "https://cryptoslate.com/feed/", rss
    "NewsBTC": "https://www.newsbtc.com/feed/",
    "Bloomberg_Crypto": "https://feeds.bloomberg.com/crypto/news.rss",
    "Glassnode_Insights": "https://glassnode.substack.com/feed",
}

TIME_WINDOW_START_UTC = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)
OUTPUT_FILE = "crypto_news_24h_zhipu_summary_v3.csv"

# ★★★ 关键修复：修复 429 Too Many Requests 错误 ★★★
# 必须设置为 1，以“串行”方式礼貌地访问，防止被服务器屏蔽。
MAX_WORKERS = 1  


# ====== ★ 抓取文本函数 (V2 升级版 - 使用 newspaper3k) ======
def extract_text_from_url(url):
    """
    使用 newspaper3k 智能提取文章正文。
    """
    try:
        # 配置 Article 对象，关闭SSL验证以增加成功率
        article = newspaper.Article(url, fetch_images=False, verbose=False)
        article.config.verify_ssl = False
        
        # 下载和解析
        article.download()
        article.parse()
        
        # 提取纯净文本
        text = article.text
        
        if not text.strip():
            tqdm.write(f"🟡 无法提取内容 (newspaper3k 未找到文本): {url}")
            return None
            
        # 限制文本长度，防止API超限
        return text[:3000] 
        
    except Exception as e:
        tqdm.write(f"⚠️ 链接抓取/提取失败 (newspaper3k)：{url} - {e}")
        return None


# ====== 智谱AI 摘要函数 (无需修改) ======
def summarize_text_zhipu(text, title):
    if not text or not text.strip():
        return ""
        
    prompt = f"你是一个加密货币新闻编辑。请用简体中文总结以下新闻，限制在2-3句话，必须包含核心事件、人物和关键数字。\n\n标题：{title}\n\n英文原文：{text[:2500]}"
    
    try:
        # 调用 智谱AI
        response = client.chat.completions.create(
            model="glm-4-air",  # 使用 glm-4-air 模型
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            timeout=20.0,  # 设置20秒超时
        )
        return response.choices[0].message.content.strip()
            
    except Exception as e:
        tqdm.write(f"❌ 智谱AI API 调用失败：{title} - {e}")
        return ""


# ====== 并发处理函数 (无需修改) ======
def process_article(entry, source):
    title = entry.title
    
    # --- 日期过滤 (无需修改) ---
    try:
        published_time_struct = entry.get("published_parsed")
        if not published_time_struct:
            tqdm.write(f"🟡 日期缺失 (跳过): {title}")
            return None
        article_timestamp_utc = calendar.timegm(published_time_struct)
        article_time_utc = datetime.datetime.fromtimestamp(article_timestamp_utc, tz=datetime.timezone.utc)
    except Exception as e:
        tqdm.write(f"🟡 日期解析失败: {entry.get('published', '')} - {e} (跳过)")
        return None
    if article_time_utc < TIME_WINDOW_START_UTC:
        return None 
    # --- 日期过滤结束 ---

    link = fix_coindesk_url(entry.link)
    date_str = entry.get("published", "") 
    
    # ★ 调用新的、更强大的抓取函数
    full_text = extract_text_from_url(link)
    
    if full_text:
        # 调用 智谱AI
        summary = summarize_text_zhipu(full_text, title)
        
        if summary:
            return {
                "标题": title, "摘要": summary, "链接": link,
                "日期": date_str, "来源": source
            }
    return None  # 抓取失败或总结失败


# ====== 主函数 (无需修改) ======
def fetch_rss_news():
    all_items = []
    tasks_to_process = []
    print(f"\n🕐 开始收集 RSS 源：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"ℹ️ 仅保留 {TIME_WINDOW_START_UTC.strftime('%Y-%m-%d %H:%M:%S')} (UTC) 之后的新闻")
    print(f"ℹ️ AI 摘要模式 (智谱AI) 已启用。")
    print(f"ℹ️ 并发数设置为 {MAX_WORKERS} (防止429错误)。") # ★ 新增日志

    # 阶段 1：收集
    rss_progress_bar = tqdm(RSS_FEEDS.items(), desc="📡 1. 扫描RSS源", unit="源", leave=False)
    for source, url in rss_progress_bar:
        rss_progress_bar.set_description(f"📡 1. 扫描中: {source}")
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                tasks_to_process.append((entry, source))
        except Exception as e:
            print(f"❌ 抓取RSS源失败：{source} - {e}")
            
    print(f"\nℹ️ 收集到 {len(tasks_to_process)} 篇文章，开始并发处理...")

    # 阶段 2：并发处理
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_article, entry, source) for entry, source in tasks_to_process]
        
        ai_progress_bar = tqdm(
            concurrent.futures.as_completed(futures),
            total=len(tasks_to_process),
            desc="🤖 2. AI 摘要处理中 (智谱AI)", 
            unit="篇"
        )
        
        for future in ai_progress_bar:
            result = future.result()
            if result:
                all_items.append(result)

    # 阶段 3：保存结果
    if all_items:
        df = pd.DataFrame(all_items)
        df = df[["标题", "摘要", "链接", "日期", "来源"]]
        df.drop_duplicates(subset=["链接"], inplace=True)
        
        try:
            df['parsed_date'] = pd.to_datetime(df['日期'], errors='coerce')
            df = df.sort_values(by='parsed_date', ascending=False).drop(columns=['parsed_date'])
        except Exception:
            print("⚠️ 日期格式不统一，未进行排序。")
            
        df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
        print(f"\n✅ 已保存 {len(df)} 条 [AI 摘要] 新闻到 {OUTPUT_FILE}")
    else:
        print(f"⚠️ 未获取到过去24小时内的新闻。")

# (修复 Coindesk 链接函数，保持不变)
def fix_coindesk_url(url: str) -> str:
    if "coindesk.com" not in url: return url
    try:
        fixed = url.replace(",", "/")
        if not fixed.startswith("https://"): fixed = "https://" + fixed.lstrip("/")
        return fixed
    except Exception: return url

# ====== 手动执行入口 ======
if __name__ == "__main__":
    start = time()
    fetch_rss_news()
    print(f"\n⏱️ 总耗时：{round(time() - start, 2)} 秒")