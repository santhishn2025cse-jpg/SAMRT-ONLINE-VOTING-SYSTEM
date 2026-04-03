def main():
    print("Welcome to your new Python project!")
    
    try:
        user_input = input("Enter your name: ")
        print(f"Hello, {user_input}! It's great to meet you.")
    except KeyboardInterrupt:
        print("\nGoodbye!")

if __name__ == "__main__":
    main()
