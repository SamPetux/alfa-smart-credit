"""Worker entrypoint (тот же backend-образ). Claim/lease — B05.

Пока B05 не готов: процесс живёт и не падает (нужен для Compose B01/B08).
"""

from __future__ import annotations

import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("worker")


def main() -> None:
    log.info("worker stub started — job claim loop will be B05")
    while True:
        time.sleep(30)
        log.info("worker idle (B05 not implemented)")


if __name__ == "__main__":
    main()
