from methods.userHandler import UserHandler
from entities.user import User

if __name__ == "__main__":
    user1 = User(1, "alice", "key123", "passAlice")
    user2 = User(2, "bob", "key456", "passBob")

    handler = UserHandler([])
    handler.add_user(user1)
    handler.add_user(user2)

    handler.print_users()