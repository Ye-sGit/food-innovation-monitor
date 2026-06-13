"""测试国外媒体 RSS 是否可用"""
import feedparser

feeds = [
    ("BakeryAndSnacks", "https://www.bakeryandsnacks.com/Info/RSS"),
    ("PlantBasedNews", "https://plantbasednews.org/feed/"),
    ("DailyCoffeeNews", "https://dailycoffeenews.com/feed/"),
    ("NOSH", "https://www.nosh.com/feed/"),
    ("TrendHunter", "https://www.trendhunter.com/feed"),
    ("ForbesFood", "https://www.forbes.com/food-drink/feed/"),
]

for name, url in feeds:
    try:
        feed = feedparser.parse(url)
        items = len(feed.entries)
        if items > 0:
            print(f"[OK] {name}: {items} items - {feed.entries[0].title[:60]}")
        else:
            err = str(feed.get('bozo_exception', ''))[:60]
            print(f"[FAIL] {name}: 0 items ({err})")
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
