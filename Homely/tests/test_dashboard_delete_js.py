from pathlib import Path


def test_dashboard_delete_js_calls_backend_delete_route():
    js_path = Path(__file__).resolve().parents[1] / "app" / "static" / "js" / "homely-tasks.js"
    text = js_path.read_text(encoding='utf-8')

    assert "fetch(`/tasks/${id}`" in text
    assert 'method: "DELETE"' in text
    assert "X-CSRFToken" in text
    assert "tasks = tasks.filter" in text
