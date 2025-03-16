import pytest

def main():
    pytest.main(["--cov=resonitepy", "--cov-report=term-missing", "--cov-report=html", "-vv"])

if __name__ == "__main__":
    main()