class UserHandler:
    def __init__(self, user_list):
        self.user_list = user_list
    
    def add_user(self, user):
        self.user_list.append(user)
    
    def print_users(self):
        for user in self.user_list:
            print(f'ID: {user.id}, Username: {user.username}')