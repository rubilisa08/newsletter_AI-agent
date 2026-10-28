"""스케줄러용 실행 진입점.

Windows 작업 스케줄러가 매일 07:30에 이 파일을 실행한다.
그래프 자체는 skeleton.py에 있고, 여기서는 실행 결과의 log를 logs/YYYY-MM-DD.log 에 남긴다.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from skeleton import run

ROOT = Path(__file__).resolve().parent


def setup_logging(run_date: str) -> None:
    log_dir = ROOT / "logs"
    log_dir.mkdir(exist_ok=True)

    handlers: list[logging.Handler] = [
        logging.FileHandler(log_dir / f"{run_date}.log", encoding="utf-8")
    ]
    # pythonw.exe(창 없이 실행)에서는 stdout이 없으므로 콘솔 출력은 있을 때만 붙인다.
    if sys.stdout is not None:
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s | %(message)s",
        handlers=handlers,
    )


def main() -> int:
    run_date = datetime.now().strftime("%Y-%m-%d")
    setup_logging(run_date)
    load_dotenv(ROOT / ".env")

    log = logging.getLogger("main")
    log.info("===== 뉴스레터 실행 시작 =====")
    try:
        result = run()
    except Exception:
        log.exception("실행 실패")
        return 1

    for line in result["log"]:
        log.info(line)
    log.info("===== 실행 완료 =====")
    return 0


if __name__ == "__main__":
    sys.exit(main())
