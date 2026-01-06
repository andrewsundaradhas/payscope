from __future__ import annotations

import os
import logging

from payscope_ingestion.logging import configure_logging


def main() -> None:
    # Production entrypoint is ASGI (uvicorn). This module remains for container smoke tests.
    configure_logging(service_name=os.getenv("SERVICE_NAME", "ingestion"))
    logging.getLogger(__name__).info("service_boot")


if __name__ == "__main__":
    main()


