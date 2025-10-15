# --- 全新代码开始 (版本 2.4 - 赛季修正+队徽修复版) ---

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

# --- 配置区 ---
API_KEY = "3"
LEAGUE_ID = "4328"
# 【【【核心修复！！！】】】 将赛季更新为当前正在进行的赛季
SEASON = "2025-2026" 
TEAM_IDS = {
    "arsenal": "133602", "liverpool": "133601",
    "man_city": "134777", "fulham": "133600",
}

# --- FastAPI 应用设置 ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# --- 辅助函数 ---
def call_api(endpoint: str, params: dict):
    base_url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/{endpoint}"
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API call failed for {endpoint}: {e}")
        return None

def format_event(event: dict) -> str:
    home = event.get('strHomeTeam', 'N/A')
    away = event.get('strAwayTeam', 'N/A')
    home_score = event.get('intHomeScore')
    away_score = event.get('intAwayScore')
    event_date_str = event.get('dateEventLocal')
    
    date_formatted = datetime.strptime(event_date_str, "%Y-%m-%d").strftime("%m月%d日") if event_date_str else "日期未知"
    
    if home_score is not None and away_score is not None:
        return f"{date_formatted}: {home} {home_score} - {away_score} {away}"
    return f"{date_formatted}: {home} vs {away}"

# --- API 端点定义 ---
@app.get("/api/sports/premier-league")
def get_premier_league_data():
    # 1. 获取积分榜
    standings_data = call_api("lookuptable.php", {"l": LEAGUE_ID, "s": SEASON})
    standings = []
    if standings_data and "table" in standings_data and standings_data["table"] is not None:
        for entry in standings_data["table"][:5]:
            logo_url = entry.get('strTeamBadge')
            # 【【【核心修复！！！】】】 去掉URL末尾的/preview，确保图片能显示
            clean_logo_url = logo_url.replace('/preview', '') if logo_url else None
            standings.append({
                "rank": entry.get('intRank', '#'),
                "team": entry.get('strTeam', '未知球队'),
                "points": entry.get('intPoints', 'N/A'),
                "logo": clean_logo_url
            })
    
    if not standings:
        standings.append({"error": "积分榜数据获取失败"})

    # 2. 获取关注球队的赛程
    tracked_teams_results = {}
    now = datetime.now(timezone.utc)
    
    for team_name, team_id in TEAM_IDS.items():
        all_events_data = call_api("eventsseason.php", {"id": team_id, "s": SEASON})
        last_match, next_matches = "无赛果数据", []
        
        if all_events_data and "events" in all_events_data and all_events_data["events"] is not None:
            valid_events = [e for e in all_events_data["events"] if e.get('strTimestamp')]
            
            if valid_events:
                events = sorted(
                    valid_events,
                    key=lambda x: datetime.fromisoformat(x['strTimestamp'].replace('Z', '+00:00'))
                )
                
                past_events = [e for e in events if datetime.fromisoformat(e['strTimestamp'].replace('Z', '+00:00')) < now]
                future_events = [e for e in events if datetime.fromisoformat(e['strTimestamp'].replace('Z', '+00:00')) >= now]
                
                if past_events:
                    last_match = format_event(past_events[-1])
                if future_events:
                    next_matches = [format_event(e) for e in future_events[:2]]

        tracked_teams_results[team_name] = {
            "last_match": last_match,
            "next_matches": next_matches if next_matches else ["无未来赛程"]
        }

    return {"standings": standings, "tracked_teams": tracked_teams_results}

@app.get("/")
def read_root():
    return {"message": "欢迎来到 DailyReport API v2.4 (最终修正版)"}

# --- 全新代码结束 ---
