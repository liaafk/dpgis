import cProfile

def main():
    print("Hello World!")
    cProfile.run("[(a, b) for a in (1, 3, 5) for b in (2, 4, 6)]")

if __name__ == "__main__":
    main()