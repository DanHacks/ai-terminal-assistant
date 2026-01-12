from platform_utils import detect_platform

def main():
    print("AI Terminal Assistant")
    print("====================")
    print(f"Platform detected: {detect_platform()}")
    print("Type 'exit' to quit")

    while True:
        user_input = input(">> ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye 👋")
            break
        print(f"You said: {user_input}")

if __name__ == "__main__":
    main()
