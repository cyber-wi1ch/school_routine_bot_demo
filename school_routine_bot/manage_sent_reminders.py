import json
from json import JSONDecodeError
from pathlib import Path

from school_routine_bot.pydantic_schemes import ValidDutyRow


class ManageSentReminders:
    def __init__(self, path_to_sent_reminders: str):
        self.sent_reminders_path = Path(__file__).parent / path_to_sent_reminders
        self.sent_reminders: dict = {}

    def get_sent_reminders(self):
        try:
            with open(self.sent_reminders_path, "r") as f:
                self.sent_reminders.update({int(k): v for k, v in json.load(f).items()})
        except (JSONDecodeError, FileNotFoundError):
            with open(self.sent_reminders_path, "w") as f:
                json.dump(self.sent_reminders, f, ensure_ascii=False)
        return self.sent_reminders

    def add_duty_to_sent_reminders(self, user_id, duty_to_add: ValidDutyRow):
        self.sent_reminders[user_id] = self.sent_reminders.get(user_id, []) + [
            duty_to_add.model_dump(mode="json")
        ]
        with open(self.sent_reminders_path, "w") as f:
            json.dump(self.sent_reminders, f, ensure_ascii=False)

    def clean_sent_reminders(self):
        self.sent_reminders = {}
        with open(self.sent_reminders_path, mode="w", encoding="utf-8") as f:
            f.write("{}")
