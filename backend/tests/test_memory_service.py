from unittest.mock import patch, MagicMock
from app.services.memory_service import check_similar_memories

def make_point(id, score, content):
    point = MagicMock()
    point.id = id
    point.score = score
    point.payload = {"content": content}
    return point

# 1. Score > 0.9, different content → returned as similar
def test_returns_similar_memory_above_threshold():
    point = make_point("abc", 0.95, "I love hiking")
    with patch("app.services.memory_service.search_points_raw") as mock:
        mock.return_value = MagicMock(points=[point])
        result = check_similar_memories("I enjoy hiking", [], user_id=1, collection_name="col")
    assert len(result) == 1
    assert result[0]["similarity"] == 0.95

# 2. Score exactly 0.9 → NOT returned (strictly > 0.9)
def test_excludes_memory_at_threshold():
    point = make_point("abc", 0.9, "I love hiking")
    with patch("app.services.memory_service.search_points_raw") as mock:
        mock.return_value = MagicMock(points=[point])
        result = check_similar_memories("I enjoy hiking", [], user_id=1, collection_name="col")
    assert result == []

# 3. Score > 0.9, but content is identical → NOT returned (exact match is handled separately upstream)
def test_excludes_exact_content_match():
    point = make_point("abc", 0.99, "I enjoy hiking")
    with patch("app.services.memory_service.search_points_raw") as mock:
        mock.return_value = MagicMock(points=[point])
        result = check_similar_memories("I enjoy hiking", [], user_id=1, collection_name="col")
    assert result == []

# 4. No points returned → empty list
def test_returns_empty_when_no_points():
    with patch("app.services.memory_service.search_points_raw") as mock:
        mock.return_value = MagicMock(points=[])
        result = check_similar_memories("anything", [], user_id=1, collection_name="col")
    assert result == []