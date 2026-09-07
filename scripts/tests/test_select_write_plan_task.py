import importlib.util
import unittest
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo


SCRIPT = Path(__file__).resolve().parents[1] / "select_write_plan_task.py"
SPEC = importlib.util.spec_from_file_location("select_write_plan_task", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class SelectWritePlanTaskTests(unittest.TestCase):
    def test_filters_by_tokyo_date_and_unstarted_state(self):
        data = {
            "tasks": [
                {
                    "siteId": MODULE.TARGET_SITE_ID,
                    "id": "selected",
                    "writePlanDate": 1787788800000,
                    "articleUrl": None,
                    "writeDoneDate": None,
                },
                {
                    "siteId": MODULE.TARGET_SITE_ID,
                    "id": "has-url",
                    "writePlanDate": 1787788800000,
                    "articleUrl": "https://fukugyojapan.com/done/",
                    "writeDoneDate": None,
                },
                {
                    "siteId": MODULE.TARGET_SITE_ID,
                    "id": "has-done-date",
                    "writePlanDate": 1787788800000,
                    "articleUrl": None,
                    "writeDoneDate": 1787788800000,
                },
                {
                    "siteId": MODULE.TARGET_SITE_ID,
                    "id": "other-date",
                    "writePlanDate": 1787702400000,
                    "articleUrl": None,
                    "writeDoneDate": None,
                },
            ]
        }

        result = MODULE.select_tasks(
            data, date(2026, 8, 27), ZoneInfo("Asia/Tokyo")
        )

        self.assertEqual([task["id"] for task in result], ["selected"])

    def test_preserves_api_order(self):
        data = {
            "tasks": [
                {
                    "siteId": MODULE.TARGET_SITE_ID,
                    "id": "first",
                    "writePlanDate": 1787788800000,
                    "articleUrl": "",
                    "writeDoneDate": "",
                },
                {
                    "siteId": MODULE.TARGET_SITE_ID,
                    "id": "second",
                    "writePlanDate": 1787788800000,
                    "articleUrl": None,
                    "writeDoneDate": None,
                },
            ]
        }

        result = MODULE.select_tasks(
            data, date(2026, 8, 27), ZoneInfo("Asia/Tokyo")
        )

        self.assertEqual([task["id"] for task in result], ["first", "second"])

    def test_excludes_other_sites_and_missing_site_id(self):
        base = {"writePlanDate": 1787788800000, "articleUrl": None, "writeDoneDate": None}
        tasks = [
            dict(base, id="other", siteId="another-site", siteName="副業JAPAN"),
            dict(base, id="missing", siteName="副業JAPAN"),
            dict(base, id="target", siteId=MODULE.TARGET_SITE_ID),
        ]
        result = MODULE.select_tasks({"tasks": tasks}, date(2026, 8, 27), ZoneInfo("Asia/Tokyo"))
        self.assertEqual([task["id"] for task in result], ["target"])


if __name__ == "__main__":
    unittest.main()
