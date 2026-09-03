"""Development entry point for the Fintech Assistant."""

from api.application import app
from utils.config import Config


def main() -> None:
    app.run(host="0.0.0.0", port=Config.PORT, debug=False)


if __name__ == "__main__":
    main()
