#!/usr/bin/env python3
"""每天从 Devpost 公开 API 取 Kiroween 参赛人数,写进小站看板(Firestore)。
由 launchd 定时调用:~/Library/LaunchAgents/com.beisai.update-stats.plist
"""
import json, sys, time, urllib.request

API_KEY = "AIzaSyC_gLfsZKaWo95hBepWsvf4AgLjp7p_hnw"  # Firebase 公开客户端 key,与网站内嵌的是同一个
DOC = "https://firestore.googleapis.com/v1/projects/hackathon2026-18d68/databases/(default)/documents/events/ev_kiroween2026"

def main():
    data = json.loads(urllib.request.urlopen(urllib.request.Request(
        "https://devpost.com/api/hackathons?search=kiroween",
        headers={"User-Agent": "beisai-stats/1.0 (personal dashboard, 1 request/day)"}),
        timeout=30).read())
    hit = next((h for h in data.get("hackathons", []) if h.get("title") == "Kiroween 2026"), None)
    if not hit or not hit.get("registrations_count"):
        print(time.strftime("%F %T"), "API 里没找到 Kiroween 2026 的人数,跳过")
        return
    count = int(hit["registrations_count"])

    tok = json.loads(urllib.request.urlopen(urllib.request.Request(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={API_KEY}",
        data=b'{"returnSecureToken":true}',
        headers={"Content-Type": "application/json"}), timeout=30).read())["idToken"]

    fields = {"participants": {"integerValue": str(count)},
              "statsUpdatedAt": {"integerValue": str(int(time.time() * 1000))}}
    mask = "&".join("updateMask.fieldPaths=" + k for k in fields)
    urllib.request.urlopen(urllib.request.Request(
        f"{DOC}?{mask}", method="PATCH",
        data=json.dumps({"fields": fields}).encode(),
        headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"}), timeout=30).read()
    print(time.strftime("%F %T"), "看板已更新,人数:", count)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(time.strftime("%F %T"), "失败:", e)
        sys.exit(1)
