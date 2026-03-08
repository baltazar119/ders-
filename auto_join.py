import datetime as dt
import os
import time
import webbrowser
from dataclasses import dataclass
from typing import List, Optional, Set

import yaml
from dotenv import load_dotenv
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

LOGIN_URL = "https://online.yildiz.edu.tr/Account/Login?ReturnUrl=%2f"
DAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

JOIN_TEXT_SELECTORS = [
    "a:has-text('Derse Katıl')",
    "button:has-text('Derse Katıl')",
    "a:has-text('Join')",
    "button:has-text('Join')",
    "a[href*='zoom.us']",
    "a[href*='zoom']",
]


@dataclass
class Course:
    name: str
    day: int
    start_time: str
    end_time: str
    lesson_url: str


def load_courses(path: str) -> List[Course]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    courses: List[Course] = []
    for row in data.get("courses", []):
        courses.append(
            Course(
                name=row["name"],
                day=DAY_MAP[row["day"].strip().lower()],
                start_time=row["start_time"],
                end_time=row["end_time"],
                lesson_url=row["lesson_url"],
            )
        )
    return courses


def _at_time(now: dt.datetime, hhmm: str) -> dt.datetime:
    hour, minute = map(int, hhmm.split(":"))
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)


def should_attempt_join(now: dt.datetime, course: Course, early_minutes: int) -> bool:
    if now.weekday() != course.day:
        return False
    start = _at_time(now, course.start_time)
    end = _at_time(now, course.end_time)
    begin = start - dt.timedelta(minutes=early_minutes)
    return begin <= now <= end


def login(page, username: str, password: str) -> None:
    page.goto(LOGIN_URL, wait_until="domcontentloaded")

    user_selectors = ['input[name="UserName"]', 'input[name="username"]', 'input[type="text"]']
    pass_selectors = ['input[name="Password"]', 'input[name="password"]', 'input[type="password"]']

    for sel in user_selectors:
        if page.locator(sel).count() > 0:
            page.fill(sel, username)
            break

    for sel in pass_selectors:
        if page.locator(sel).count() > 0:
            page.fill(sel, password)
            break

    if page.locator('button[type="submit"]').count() > 0:
        page.click('button[type="submit"]')
    elif page.locator('input[type="submit"]').count() > 0:
        page.click('input[type="submit"]')
    else:
        raise RuntimeError("Giriş butonu bulunamadı.")

    page.wait_for_load_state("networkidle")


def find_join_target(page) -> Optional[tuple]:
    for selector in JOIN_TEXT_SELECTORS:
        loc = page.locator(selector)
        if loc.count() > 0:
            item = loc.first
            href = item.get_attribute("href") or ""
            return item, href
    return None


def open_join_target(locator, href: str) -> bool:
    if href.startswith("http"):
        webbrowser.open(href)
        return True
    try:
        locator.click(timeout=2500)
        return True
    except PlaywrightTimeoutError:
        return False


def wait_and_join_lesson(page, course: Course, poll_seconds: int, timeout_minutes: int) -> bool:
    deadline = dt.datetime.now() + dt.timedelta(minutes=timeout_minutes)

    while dt.datetime.now() < deadline:
        page.goto(course.lesson_url, wait_until="domcontentloaded")
        target = find_join_target(page)
        if target:
            locator, href = target
            if open_join_target(locator, href):
                print(f"[JOINED] {course.name} -> Zoom/Derse Katıl açıldı.")
                return True
        print(f"[WAIT] {course.name} için link henüz görünmüyor, {poll_seconds}s sonra tekrar.")
        time.sleep(poll_seconds)

    print(f"[TIMEOUT] {course.name} için katılma bağlantısı bulunamadı.")
    return False


def run() -> None:
    load_dotenv()

    username = os.getenv("ONLINE_USERNAME")
    password = os.getenv("ONLINE_PASSWORD")
    loop_interval_seconds = int(os.getenv("CHECK_INTERVAL_SECONDS", "30"))
    join_early_minutes = int(os.getenv("JOIN_EARLY_MINUTES", "10"))
    join_poll_seconds = int(os.getenv("JOIN_POLL_SECONDS", "15"))
    lesson_wait_timeout_minutes = int(os.getenv("LESSON_WAIT_TIMEOUT_MINUTES", "45"))
    headless = os.getenv("HEADLESS", "false").lower() == "true"

    if not username or not password:
        raise RuntimeError("ONLINE_USERNAME ve ONLINE_PASSWORD .env içinde zorunludur.")

    courses = load_courses("timetable.yaml")
    joined_today: Set[str] = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        login(page, username, password)
        print("[INFO] Giriş başarılı, ders bazlı izleme başladı.")

        while True:
            now = dt.datetime.now()
            active_courses = [c for c in courses if should_attempt_join(now, c, join_early_minutes)]

            for course in active_courses:
                key = f"{now.date()}::{course.name}::{course.start_time}"
                if key in joined_today:
                    continue

                if wait_and_join_lesson(page, course, join_poll_seconds, lesson_wait_timeout_minutes):
                    joined_today.add(key)

            time.sleep(loop_interval_seconds)


if __name__ == "__main__":
    run()
