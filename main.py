# Filename: main.py

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# 创建FastAPI应用实例
app = FastAPI()

# 【重要】配置CORS中间件，允许所有来源的跨域请求。
# 这是为了让部署在Render上的前端可以访问这个后端API。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有HTTP头
)

# 定义一个数据抓取函数
def scrape_premier_league_data():
    """
    抓取英超关键数据。
    数据源：Google Sports (结构简单，适合静态抓取)
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    # 使用更具体的搜索词以获得更稳定的结果
    url = "https://www.google.com/search?q=premier+league+table"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 如果请求失败则抛出异常
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. 抓取积分榜 (前5)
        standings = []
        # 注意：这些选择器(selector)是前端代码的“地址”，可能会因Google页面更新而改变
        # 我们选择一个相对稳定的父容器来查找
        table_container = soup.find('div', class_='Jzru1c') 
        if table_container:
            table_rows = table_container.select('table tbody tr')
            for row in table_rows[:5]: # 只取前5行
                cells = row.find_all('td')
                if len(cells) > 1:
                    # 提取数据时进行清理，去除不必要的空格
                    rank = cells[0].get_text(strip=True)
                    team_name_div = cells[1].find('div', class_='vT3p7e')
                    team = team_name_div.get_text(strip=True) if team_name_div else 'N/A'
                    points_divs = cells[-1].find_all('div')
                    points = points_divs[-1].get_text(strip=True) if points_divs else 'N/A'

                    standings.append(f"{rank}. {team} ({points}分)")

        return {
            "standings": standings if standings else ["积分榜数据抓取失败，请检查后端日志。"],
            "top_scorers": ["功能开发中..."],
            "assists_leaders": ["功能开发中..."],
            "tracked_teams": {
                "arsenal": {"last_match": "赛程数据抓取开发中...", "next_matches": []},
                "liverpool": {"last_match": "赛程数据抓取开发中...", "next_matches": []},
                "man_city": {"last_match": "赛程数据抓取开发中...", "next_matches": []},
                "fulham": {"last_match": "赛程数据抓取开发中...", "next_matches": []},
            }
        }

    except requests.exceptions.RequestException as e:
        # 如果网络请求或HTML解析出错，返回详细的错误信息
        raise HTTPException(status_code=500, detail=f"抓取数据时发生网络错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理数据时发生未知错误: {str(e)}")


# 创建API端点 (Endpoint)
@app.get("/api/sports/premier-league")
def get_premier_league_data():
    """
    提供英超数据的API接口。
    """
    return scrape_premier_league_data()

# 根路径的欢迎信息
@app.get("/")
def read_root():
    return {"message": "欢迎来到 DailyReport API"}