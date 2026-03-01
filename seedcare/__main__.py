"""python -m seedcare のエントリポイント。"""

import logging

from seedcare.collector import MQTTCollector
from seedcare.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)


def main():
    config = load_config()
    collector = MQTTCollector(config)
    collector.start()


if __name__ == "__main__":
    main()
