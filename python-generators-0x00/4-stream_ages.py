SELECT * FROM user_data LIMIT {page_size} OFFSET {offset}
def lazy_paginate(page_size):
    offset = 0
    while True:
        page = paginate_users(page_size, offset)
        if not page:
            break
        yield page
        offset += page_size
{'user_id': '00234e50...', 'name': 'Dan Altenwerth Jr.', 'email': '
 
 def stream_user_ages()
