from datetime import datetime


def pytest_html_report_title(report):
    report.title = f"Fintech Assistant - Test Report ({datetime.now().strftime('%Y-%m-%d %H:%M')})"


def pytest_configure(config):
    config._metadata = {
        "Project": "Fintech Assistant",
        "Test Suite": "Unit Tests",
    }
