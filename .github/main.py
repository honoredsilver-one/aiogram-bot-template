import os
import re
import sqlite3
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import Message

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

conn = sqlite3.connect("tasks.db")
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER,
    chat_id INTEGER,
    author_username TEXT,
    assignee_username TEXT,
    assignee_link TEXT,
    task_text TEXT,
    deadline DATETIME,
    created_at DATETIME,
    status TEXT,
    completed_at DATETIME,
    reschedule_reason TEXT
)
''')
conn.commit()

task_pattern = re.compile(
    r"@(?P<assignee_username>\w+)(?:\s+\((?P<assignee_link>https://t\.me/\w+)\))?\s+(?P<task_text>.+?)\s+DL\s+(?P<deadline>[\d.:-\s]+)",
    re.IGNORECASE
)

@dp.message_handler(lambda message: "DL" in message.text)
async def handle_task_message(message: Message):
    match = task_pattern.search(message.text)
    if not match:
        return
    deadline_str = match.group("deadline").strip()
    try:
        if "-" in deadline_str:
            deadline = datetime.strptime(deadline_str, "%d.%m - %H:%M")
            deadline = deadline.replace(year=datetime.now().year)
        else:
            deadline = datetime.strptime(deadline_str, "%H:%M")
            deadline = datetime.combine(datetime.today(), deadline.time())
    except Exception:
        deadline = datetime.now() + timedelta(hours=1)

    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tasks (
            message_id, chat_id, author_username,
            assignee_username, assignee_link, task_text,
            deadline, created_at, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        message.message_id,
        message.chat.id,
        message.from_user.username,
        match.group("assignee_username"),
        match.group("assignee_link"),
        match.group("task_text"),
        deadline,
        datetime.now(),
        'pending'
    ))
    conn.commit()
    await message.reply("✅ Задача зарегистрирована. Будут напоминания и контроль.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
