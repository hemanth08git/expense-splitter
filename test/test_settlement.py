from app.non_crud_lib.settlement import calculate_settlement

def test_calculate_settlement_simple():
    rows = [(1, 10), (2, 20)]
    result = calculate_settlement(rows)
    assert result[1] == -5.0
    assert result[2] == 5.0
