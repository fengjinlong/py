import feedparser
import pandas as pd
import datetime
import time
import concurrent.futures
import sys
import calendar
from tqdm import tqdm
import cloudscraper  # ★ 1. 导入新库

# --- AI 和网页抓取库已全部移除 ---

# ====== 配置区域 ======
RSS_FEEDS = {
    # ok
    # "CoinDesk": "",
    # 'c1':'https://www.coindesk.com/arc/outboundfeeds/rss',
    # 'c2':'https://cointelegraph.com/rss/category/op-ed',
    # 'c3':'https://cointelegraph.com/rss/category/hodlers-digest',
    # 'c4':'https://cointelegraph.com/rss/category/markets',
    # 'c5':'https://cointelegraph.com/rss',
    # 'c6':'https://thedefiant.io/feed/',
    # 'c7':'https://cryptonews.com/news/feed',
    # 'c9':'https://coinjournal.net/news/feed',
    # "Decrypt": "https://decrypt.co/feed",
    # "CryptoSlate": "https://cryptoslate.com/feed/",
    "NewsBTC": "https://rss.app/feeds/uVF07JHLgdFpr61J.xml",
    # "Bloomberg_Crypto": "https://feeds.bloomberg.com/crypto/news.rss",
    # "Reuters_Finance": "https://www.reuters.com/markets/finance/rss/",
    # "Glassnode_Insights": "https://glassnode.substack.com/feed",
    # "CryptoQuant_Blog": "https://cryptoquant.com/feed",
    # "Dune_Blog": "https://dune.com/blog/rss.xml",
    # "Messari_All": "https://messari.io/rss/all.xml",
    # "Delphi_Digital": "https://members.delphidigital.io/feed",
    # "a16z_Crypto_Blog": "https://a16zcrypto.com/feed/",
    # "Paradigm_Blog": "https://www.paradigm.xyz/rss",
    # "Coindesk_Korea": "https://www.coindeskkorea.com/rss/allArticle.xml"
}

# 浏览器伪装头 (仍然需要)
BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
}

TIME_WINDOW_START_UTC = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)
OUTPUT_FILE = "crypto_news_TEST.csv" 
MAX_WORKERS = 20


# ====== 修复 Coindesk 链接 (保留) ======
def fix_coindesk_url(url: str) -> str:
    if "coindesk.com" not in url: return url
    try:
        fixed = url.replace(",", "/")
        if not fixed.startswith("https://"): fixed = "https://" + fixed.lstrip("/")
        return fixed
    except Exception: return url

# ====== 并发处理函数 (不变) ======
def process_article(entry, source):
    """
    只进行日期过滤，不抓取网页，不调用AI
    """
    title = entry.get('title', 'No Title Provided')
    
    # --- 日期过滤 (保留) ---
    article_time_utc = None
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
    date_str = entry.get("published", "") # 这是 Published 字段
    
    return {
        "Title": title,
        "Summary": "", 
        "Link": link,
        "Published": date_str,
        "Source": source,
        "Date Batch": article_time_utc.strftime("%Y年%m月%d日"), 
        "Description": "", 
    }


# ====== ★ 核心修改点：主函数（使用 cloudscraper） ======
def fetch_rss_news():
    all_items = []
    tasks_to_process = []
    print(f"\n🕐 开始收集 RSS 源：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"ℹ️ 仅保留 {TIME_WINDOW_START_UTC.strftime('%Y-%m-%d %H:%M:%S')} (UTC) 之后的新闻")
    print("ℹ️ AI 摘要模式 (已关闭)。")

    # ★ 2. 创建一个 scraper 实例
    # (browser='chrome' 可以模拟更真实的浏览器指纹)
    scraper = cloudscraper.create_scraper(browser='chrome') 

    # 阶段 1：收集 (★ 目标1: 验证RSS源)
    rss_progress_bar = tqdm(RSS_FEEDS.items(), desc="📡 1. 扫描RSS源", unit="源", leave=False)
    for source, url in rss_progress_bar:
        rss_progress_bar.set_description(f"📡 1. 扫描中: {source}")
        try:
            # ★ 3. 使用 scraper.get() 来下载内容
            response = scraper.get(url, headers=BROWSER_HEADERS, timeout=15)
            
            # 检查HTTP状态码
            if response.status_code != 200:
                print(f"❌ 抓取失败 (HTTP {response.status_code})：{source}")
                continue # 跳过这个源

            # ★ 4. 把下载好的文本 (response.text) 喂给 feedparser
            feed = feedparser.parse(response.text) 
            
            if feed.bozo:
                # 这里的 bozo 错误现在更可能是真实的XML格式问题
                print(f"⚠️ 解析警告：{source} (RSS格式可能不规范) - {feed.bozo_exception}")
                
            if not feed.entries:
                 tqdm.write(f"🟡 源内容为空：{source} (可能抓取被拦截或该源无新闻)")
            
            for entry in feed.entries:
                tasks_to_process.append((entry, source))
                
        except Exception as e:
            # 这里的日志会捕获超时、连接错误等
            print(f"❌ 抓取RSS源时发生意外错误：{source} - {e}")
            
    print(f"\nℹ️ 收集到 {len(tasks_to_process)} 篇文章，开始并发处理...")

    # 阶段 2：并发处理 (不变)
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_article, entry, source) for entry, source in tasks_to_process]
        
        ai_progress_bar = tqdm(
            concurrent.futures.as_completed(futures),
            total=len(tasks_to_process),
            desc="📰 2. RSS 条目处理中", 
            unit="篇"
        )
        
        for future in ai_progress_bar:
            result = future.result()
            if result:
                all_items.append(result)

    # 阶段 3：保存结果 (不变)
    if all_items:
        df = pd.DataFrame(all_items)
        
        final_columns = [
            "Title", "Date Batch", "Description", "Link", 
            "Published", "Source", "Summary"
        ]
        present_columns = [col for col in final_columns if col in df.columns]
        df = df[present_columns] 
        
        df.drop_duplicates(subset=["Link"], inplace=True)
        
        try:
            df['parsed_date'] = pd.to_datetime(df['Published'], errors='coerce')
            df = df.sort_values(by='parsed_date', ascending=False).drop(columns=['parsed_date'])
        except Exception:
            print("⚠️ 日期格式不统一，未进行排序。")
            
        df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
        print(f"\n✅ 已保存 {len(df)} 条新闻条目到 {OUTPUT_FILE}")
    else:
        print(f"⚠️ 未获取到过去24小时内的新闻。")


# ====== 手动执行入口 ======
if __name__ == "__main__":
    start = time.time()
    fetch_rss_news()
    print(f"\n⏱️ 总耗时：{round(time.time() - start, 2)} 秒")