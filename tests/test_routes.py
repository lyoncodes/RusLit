from app import app

def test_render_form(client):
    response = client.get('/form')
    assert response.status_code == 200
    assert b'Your Form Title' in response.data  # Replace with actual title in form.html

def test_submit_form(client):
    response = client.post('/form', data={'field_name': 'test_value'})  # Replace 'field_name' with actual field name
    assert response.status_code == 302  # Assuming a redirect after form submission
    assert response.location == 'http://localhost/success'  # Replace with actual redirect location after submission