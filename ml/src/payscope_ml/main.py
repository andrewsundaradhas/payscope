from __future__ import annotations

import os
import logging

from payscope_ml.logging import configure_logging


def main() -> None:
    configure_logging(service_name=os.getenv("SERVICE_NAME", "ml"))
    logging.getLogger(__name__).info("service_boot")


if __name__ == "__main__":
    main()




