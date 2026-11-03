from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_review_uploaded_python_file():
    code = """
def calculate():
    eval("2 + 2")
"""

    upload_response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "sample.py",
                code,
                "text/x-python",
            )
        },
    )

    assert upload_response.status_code == 201

    upload_id = upload_response.json()["upload_id"]

    review_response = client.post(
        f"/api/v1/review/{upload_id}"
    )

    assert review_response.status_code == 200

    data = review_response.json()

    assert data["upload_id"] == upload_id
    assert data["total_issues"] >= 1
    assert data["review_provider"] == "rule_based"

    assert any(
        issue["rule_id"] == "PY002"
        for issue in data["reviews"]
    )


def test_review_invalid_upload_id():
    response = client.post(
        "/api/v1/review/invalid-id"
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_UPLOAD_ID"


def test_review_missing_upload():
    response = client.post(
        "/api/v1/review/00000000000000000000000000000000"
    )

    assert response.status_code == 404