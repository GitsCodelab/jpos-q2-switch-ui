from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
import textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class WorkerResult:
    worker_id: int
    sent: int
    approved_00: int
    security_96: int


def _java_classpath() -> str:
    cp_file = PROJECT_ROOT / ".cp.txt"
    if not cp_file.exists():
        raise FileNotFoundError(
            ".cp.txt not found. Run Maven build once to generate dependencies."
        )
    deps = cp_file.read_text(encoding="utf-8").strip()
    return f"{deps}:target/classes"


def _compile_loader(tmp_dir: Path, cp: str) -> None:
    java_src = textwrap.dedent(
        """
        import org.jpos.iso.ISOMsg;
        import org.jpos.iso.ISOUtil;
        import org.jpos.iso.channel.ASCIIChannel;
        import org.jpos.iso.packager.GenericPackager;

        public class PyIsoLoadProbe {
            public static void main(String[] args) throws Exception {
                int total = Integer.parseInt(args[0]);
                int stanStart = Integer.parseInt(args[1]);
                String rrnPrefix = args[2];
                String terminal = args[3];
                String amount = args[4];

                int approved00 = 0;
                int security96 = 0;

                GenericPackager p = new GenericPackager("cfg/iso87.xml");
                ASCIIChannel ch = new ASCIIChannel("127.0.0.1", 9000, p);
                ch.connect();

                for (int i = 0; i < total; i++) {
                    String stan = String.format("%06d", stanStart + i);
                    String rrn = rrnPrefix + String.format("%03d", i % 1000);

                    ISOMsg m = new ISOMsg();
                    m.setPackager(p);
                    m.setMTI("0200");
                    m.set(3, "000000");
                    m.set(4, amount);
                    m.set(11, stan);
                    m.set(37, rrn);
                    m.set(41, terminal);
                    // Keep security payload fixed to exercise runtime security checks.
                    m.set(52, ISOUtil.hex2byte("0123456789ABCDE0"));

                    ch.send(m);
                    ISOMsg r = ch.receive();

                    String rc = r.getString(39);
                    if ("00".equals(rc)) {
                        approved00++;
                    } else if ("96".equals(rc)) {
                        security96++;
                    }
                }

                ch.disconnect();
                System.out.println("SENT=" + total);
                System.out.println("RC00=" + approved00);
                System.out.println("RC96=" + security96);
            }
        }
        """
    ).strip()

    src = tmp_dir / "PyIsoLoadProbe.java"
    src.write_text(java_src, encoding="utf-8")

    run = subprocess.run(
        ["javac", "-cp", cp, str(src)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if run.returncode != 0:
        raise RuntimeError(run.stderr or run.stdout)


def _run_worker(
    worker_id: int,
    hits: int,
    stan_start: int,
    rrn_prefix: str,
    terminal: str,
    amount: str,
    cp: str,
    tmp_dir: Path,
) -> WorkerResult:
    run = subprocess.run(
        [
            "java",
            "-cp",
            f"{cp}:{tmp_dir}",
            "PyIsoLoadProbe",
            str(hits),
            str(stan_start),
            rrn_prefix,
            terminal,
            amount,
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if run.returncode != 0:
        raise RuntimeError(
            f"Worker {worker_id} failed:\nSTDOUT:\n{run.stdout}\nSTDERR:\n{run.stderr}"
        )

    sent = 0
    rc00 = 0
    rc96 = 0
    for line in run.stdout.splitlines():
        if line.startswith("SENT="):
            sent = int(line.split("=", 1)[1])
        elif line.startswith("RC00="):
            rc00 = int(line.split("=", 1)[1])
        elif line.startswith("RC96="):
            rc96 = int(line.split("=", 1)[1])

    return WorkerResult(worker_id=worker_id, sent=sent, approved_00=rc00, security_96=rc96)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate runtime ISO hit load from Python against jPOS Q2 listener (127.0.0.1:9000)."
    )
    parser.add_argument("--hits", type=int, default=100, help="Total hit count across all workers.")
    parser.add_argument("--workers", type=int, default=4, help="Number of concurrent workers.")
    parser.add_argument(
        "--terminal",
        default="TERM0001",
        help="Terminal ID sent in field 41 (default: TERM0001).",
    )
    parser.add_argument(
        "--amount",
        default="000000000100",
        help="Field 4 amount in ISO minor units string (default: 000000000100).",
    )
    args = parser.parse_args()

    if args.hits <= 0:
        raise ValueError("--hits must be > 0")
    if args.workers <= 0:
        raise ValueError("--workers must be > 0")
    if shutil.which("javac") is None or shutil.which("java") is None:
        raise RuntimeError("javac/java are required in PATH")

    cp = _java_classpath()

    base = args.hits // args.workers
    extra = args.hits % args.workers

    print(f"Starting ISO hit load: hits={args.hits}, workers={args.workers}")

    with tempfile.TemporaryDirectory(prefix="pyiso-load-") as tmp:
        tmp_dir = Path(tmp)
        _compile_loader(tmp_dir, cp)

        futures = []
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            stan_cursor = 810000
            for worker_id in range(args.workers):
                worker_hits = base + (1 if worker_id < extra else 0)
                if worker_hits == 0:
                    continue
                rrn_prefix = f"95{worker_id:02d}{(stan_cursor % 10000):04d}"[:9]
                futures.append(
                    pool.submit(
                        _run_worker,
                        worker_id,
                        worker_hits,
                        stan_cursor,
                        rrn_prefix,
                        args.terminal,
                        args.amount,
                        cp,
                        tmp_dir,
                    )
                )
                stan_cursor += worker_hits + 50

            total_sent = 0
            total_00 = 0
            total_96 = 0
            for future in as_completed(futures):
                result = future.result()
                total_sent += result.sent
                total_00 += result.approved_00
                total_96 += result.security_96
                print(
                    f"worker={result.worker_id} sent={result.sent} rc00={result.approved_00} rc96={result.security_96}"
                )

    print("Load run complete")
    print(f"TOTAL_SENT={total_sent}")
    print(f"TOTAL_RC00={total_00}")
    print(f"TOTAL_RC96={total_96}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
