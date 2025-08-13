import sys

def is_prime(n: int) -> bool:
    """Check if a number is prime."""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python prime-checker.py <number>")
        sys.exit(1)
    try:
        number = int(sys.argv[1])
    except ValueError:
        print("Please provide an integer.")
        sys.exit(1)
    if is_prime(number):
        print(f"{number} is a prime number.")
    else:
        print(f"{number} is not a prime number.")


if __name__ == "__main__":
    main()
