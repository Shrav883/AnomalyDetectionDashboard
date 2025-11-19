from urllib.parse import quote_plus

password = input("enter real sql password: ")
print("Encoded password: ")
print(quote_plus(password))