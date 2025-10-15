# Filename: main.py (Version 2.0 - API Edition)

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# --- 配置区 ---
API_KEY = "3"  # TheSportsDB 提供的免费公共API密钥
LEAGUE_ID = "4328"  # 英超联赛 (Premier League) 的ID
SEASON = "2025-2026" # 当前赛季
TEAM_IDS = {
    "arsenal": "133602",
    "liverpool": "133601",
    "man_city": "134777",
    "fulham": "133600",
}

# --- FastAPI 应用设置 ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# --- 辅助函数：用于调用API和格式化数据 ---

def call_api(endpoint: str, params: dict):
    """一个通用的API请求函数"""
    base_url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/{endpoint}"
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        # 如果网络请求失败，返回None
        print(f"API call failed for {endpoint}: {e}") # 在后端日志中打印错误
        return None

def format_event(event: dict) -> str:
    """将API返回的比赛数据格式化为一行可读的字符串"""
    try:
        home = event.get('strHomeTeam', 'N/A')
        away = event.get('strAwayTeam', 'N/A')
        home_score = event.get('intHomeScore', '?')
        away_score = event.get('intAwayScore', '?')
        
        # 格式化日期
        event_date_str = event.get('dateEvent')
        if event_date_str:
            event_date = datetime.strptime(event_date_str, "%Y-%m-%d")
            date_formatted = event_date.strftime("%m月%d日")
        else:
            date_formatted = "日期未知"

        # 如果比赛已结束，显示比分；否则显示对阵双方
        if home_score is not None and away_score is not None:
            return f"{date_formatted}: {home} {home_score} - {away_score} {away}"
        else:
            return f"{date_formatted}: {home} vs {away}"
    except Exception:
        return "比赛数据格式化错误"


# --- API 端点定义 ---

@app.get("/api/sports/premier-league")
def get_premier_league_data():
    """
    提供英超数据的API接口 (V2 - TheSportsDB)
    """
    # 1. 获取积分榜
    standings_data = call_api("lookuptable.php", {"l": LEAGUE_ID, "s": SEASON})
    standings = []
    if standings_data and "table" in standings_data:
        # 只取前5名
        for entry in standings_data["table"][:5]:
            team = entry.get('strTeam', '未知球队')
            points = entry.get('intPoints', 'N/A')
            rank = entry.get('intRank', '#')
            standings.append(f"{rank}. {team} ({points}分)")
    else:
        standings.append("积分榜数据获取失败")

    # 2. 获取关注球队的赛程
    tracked_teams_results = {}
    for team_name, team_id in TEAM_IDS.items():
        # 获取上一场比赛
        last_match_data = call_api("eventslast.php", {"id": team_id})
        last_match_str = "无上一场比赛数据"
        if last_match_data and "results" in last_match_data:
            last_match_str = format_event(last_match_data["results"][0])

        # 获取未来两场比赛
        next_matches_data = call_api("eventsnext.php", {"id": team_id})
        next_matches_list = []
        if next_matches_data and "events" in next_matches_data:
            # 只取未来两场
            for event in next_matches_data["events"][:2]:
                next_matches_list.append(format_event(event))
        
        tracked_teams_results[team_name] = {
            "last_match": last_match_str,
            "next_matches": next_matches_list if next_matches_list else ["无未来赛程数据"]
        }

    # 3. 整合最终结果
    # 务实说明：射手榜和助攻榜是付费API功能，免费版无法获取
    return {
        "standings": standings,
        "top_scorers": ["射手榜需付费API，功能待定"],
        "assists_leaders": ["助攻榜需付费API，功能待定"],
        "tracked_teams": tracked_teams_results,
    }

@app.get("/")
def read_root():
    return {"message": "欢迎来到 DailyReport API v2.0"}