from pymongo import MongoClient
from werkzeug.security import check_password_hash

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['userdb']
users_collection = db['users']

def check_users():
    users = list(users_collection.find())
    print("\nAll users in database:")
    print("-" * 90)
    print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Phone':<15} {'Is Admin':<10}")
    print("-" * 90)
    for user in users:
        print(f"{str(user['_id'])[:5]:<5} {user['username']:<20} {user['email']:<30} {str(user.get('phone', '-')):<15} {str(user.get('is_admin', False)):<10}")
    print("-" * 90)
    print(f"Total users: {len(users)}")

def verify_user_credentials(username, password):
    user = users_collection.find_one({'username': username})
    if user and check_password_hash(user['password'], password):
        print("\nCredentials are valid!")
        return True
    print("\nInvalid credentials!")
    return False

def find_user(username=None, email=None):
    query = {}
    if username:
        query['username'] = username
    elif email:
        query['email'] = email
    else:
        print("Please provide either username or email")
        return

    user = users_collection.find_one(query)
    if user:
        print("\nUser found:")
        print("-" * 50)
        print(f"ID: {user['_id']}")
        print(f"Username: {user['username']}")
        print(f"Email: {user['email']}")
        print(f"Is Admin: {user.get('is_admin', False)}")
        print("-" * 50)
    else:
        print("\nUser not found!")

if __name__ == "__main__":
    print("\n=== Database User Management ===")
    print("1. List all users")
    print("2. Verify user credentials")
    print("3. Find user by username")
    print("4. Find user by email")
    
    choice = input("\nEnter your choice (1-4): ")
    
    if choice == "1":
        check_users()
    elif choice == "2":
        username = input("Enter username: ")
        password = input("Enter password: ")
        verify_user_credentials(username, password)
    elif choice == "3":
        username = input("Enter username to find: ")
        find_user(username=username)
    elif choice == "4":
        email = input("Enter email to find: ")
        find_user(email=email)
    else:
        print("Invalid choice!")