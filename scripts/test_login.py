from app import app

client = app.test_client()

admin_login = client.post('/api/login', json={'username': 'admin', 'password': 'admin123', 'role': 'admin'})
print('admin_login', admin_login.status_code, admin_login.get_json())
assert admin_login.status_code == 200, 'Admin login failed.'
assert admin_login.get_json()['role'] == 'admin', 'Admin role mismatch.'

logout = client.post('/api/logout')
print('logout', logout.status_code, logout.get_json())
assert logout.status_code == 200, 'Logout failed.'

user_login = client.post('/api/login', json={'username': 'user', 'password': 'user123', 'role': 'user'})
print('user_login', user_login.status_code, user_login.get_json())
assert user_login.status_code == 200, 'User login failed.'
assert user_login.get_json()['role'] == 'user', 'User role mismatch.'

page = client.get('/')
print('home_status', page.status_code)
assert page.status_code == 200, 'Home page should load for logged-in users.'
