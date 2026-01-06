from __future__ import annotations

import os
import logging

from payscope_agents.logging import configure_logging


def main() -> None:
    configure_logging(service_name=os.getenv("SERVICE_NAME", "agents"))
    logging.getLogger(__name__).info("service_boot")


if __name__ == "__main__":
    main()




