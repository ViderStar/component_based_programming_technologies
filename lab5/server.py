"""`python -m lab5.server`: build the war, start Tomcat and keep it running until Ctrl+C."""

from __future__ import annotations

import threading

from lab5.runtime import Tomcat


def main() -> None:
    tomcat = Tomcat()
    tomcat.start()
    print(f"Lab 5 site: {tomcat.url}", flush=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        tomcat.stop()


if __name__ == "__main__":
    main()
