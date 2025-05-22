from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(f"Your new Fernet key is: {key.decode()}")
print("Copy this key and add it to your .env file as JIRA_TOKEN_ENCRYPTION_KEY.")
