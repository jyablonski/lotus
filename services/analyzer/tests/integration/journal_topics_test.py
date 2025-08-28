def test_analyze_endpoint(client_fixture):
    response = client_fixture.post(
        "/v1/journals/3/topics",
        json={"text": "Had a relaxing evening reading a good book and drinking tea."},
    )

    assert response.status_code == 204
