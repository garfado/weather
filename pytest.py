def test_fetch_weather_data():
    data = fetch_weather_data()
    assert "times" in data
    assert "temperatures" in data
    assert len(data["times"]) == len(data["temperatures"])