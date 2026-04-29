from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_ISO_MESSAGE = {
    "mti": "0200",
    "3": "000000",
    "4": "000000000100",
    "11": "123456",
    "37": "123456789012",
    "41": "TERM0001",
    "2": "1234567890123456",
}

# Device profiles for ISO testing
PROFILES = {
    "atm": {
        "mti": "0200",
        "3": "011000",  # ATM withdrawal
        "4": "000000010000",  # 100.00 in minor units
        "22": "021",  # ATM interface mode
        "41": "ATM0001",
        "description": "ATM withdrawal transaction",
    },
    "pos": {
        "mti": "0200",
        "3": "000000",  # Goods and services
        "4": "000000005000",  # 50.00 in minor units
        "22": "022",  # POS interface mode
        "41": "POS0001",
        "description": "POS purchase transaction",
    },
    "reversal": {
        "mti": "0420",  # Reversal request
        "3": "000000",
        "4": "000000001000",
        "11": "654321",  # Different STAN
        "37": "987654321098",  # Different RRN
        "41": "TERM-REV",
        "description": "Transaction reversal request",
    },
    "fraud": {
        "mti": "0200",
        "3": "000000",
        "4": "000000999999",  # High amount 9999.99
        "22": "029",  # Suspicious mode
        "41": "TERM9999",  # Blacklisted terminal
        "2": "9999999999999999",  # Suspicious PAN
        "description": "High-risk fraud test transaction",
    },
}


def _java_classpath() -> str:
    cp_file = PROJECT_ROOT / ".cp.txt"
    if not cp_file.exists():
        raise FileNotFoundError(".cp.txt not found. Run Maven build once to generate dependencies.")
    deps = cp_file.read_text(encoding="utf-8").strip()
    return f"{deps}:target/classes"


def _compile_probe(tmp_dir: Path, cp: str) -> None:
    java_src = textwrap.dedent(
        """
        import org.jpos.iso.ISOMsg;
        import org.jpos.iso.channel.ASCIIChannel;
        import org.jpos.iso.packager.GenericPackager;

        public class PySingleIsoProbe {
            public static void main(String[] args) throws Exception {
                GenericPackager packager = new GenericPackager("cfg/iso87.xml");
                ASCIIChannel channel = new ASCIIChannel("127.0.0.1", 9000, packager);
                channel.connect();

                ISOMsg m = new ISOMsg();
                m.setPackager(packager);
                m.setMTI(args[0]);
                for (int i = 1; i + 1 < args.length; i += 2) {
                    int field = Integer.parseInt(args[i]);
                    m.set(field, args[i + 1]);
                }

                channel.send(m);
                ISOMsg r = channel.receive();
                System.out.println("MTI=" + r.getMTI());
                System.out.println("RC=" + r.getString(39));
                System.out.println("STAN=" + r.getString(11));
                System.out.println("RRN=" + r.getString(37));

                channel.disconnect();
            }
        }
        """
    ).strip()

    src = tmp_dir / "PySingleIsoProbe.java"
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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send a single ISO8583 message to the running jPOS listener at 127.0.0.1:9000",
        epilog="Profiles: atm, pos, reversal, fraud (shorthand device presets)",
    )
    parser.add_argument(
        "--profile",
        choices=list(PROFILES.keys()),
        default=None,
        help="Use a preset device profile (ATM, POS, Reversal, Fraud) with predefined fields.",
    )
    parser.add_argument(
        "--iso",
        help="JSON object for ISO message fields. Example: '{\"mti\":\"0200\",\"11\":\"100001\"}'",
    )
    parser.add_argument(
        "--mti",
        default=None,
        help="Override MTI only (default from built-in message: 0200).",
    )
    parser.add_argument(
        "--field",
        action="append",
        default=[],
        help="Override a field as key=value, can be repeated (example: --field 4=000000010000).",
    )
    return parser.parse_args()


def _build_message(args: argparse.Namespace) -> dict[str, str]:
    # Start with defaults
    msg = dict(DEFAULT_ISO_MESSAGE)

    # Apply profile if specified
    if args.profile:
        profile = PROFILES[args.profile]
        for key, value in profile.items():
            if key != "description":
                msg[key] = str(value)

    # Apply --iso JSON override
    if args.iso:
        parsed = json.loads(args.iso)
        for key, value in parsed.items():
            msg[str(key)] = str(value)

    # Apply --mti override
    if args.mti:
        msg["mti"] = args.mti

    # Apply individual --field overrides
    for item in args.field:
        if "=" not in item:
            raise ValueError(f"Invalid --field format: {item}")
        key, value = item.split("=", 1)
        msg[key.strip()] = value.strip()

    if "mti" not in msg:
        msg["mti"] = "0200"

    return msg


def main() -> int:
    args = _parse_args()
    if shutil.which("javac") is None or shutil.which("java") is None:
        raise RuntimeError("javac/java are required in PATH")

    message = _build_message(args)
    cp = _java_classpath()

    if args.profile:
        print(f"Using profile: {args.profile}")
        print(f"Description: {PROFILES[args.profile].get('description', '')}")
    print("\nSending ISO message:")
    print(json.dumps(message, indent=2))

    with tempfile.TemporaryDirectory(prefix="py-single-iso-") as tmp:
        tmp_dir = Path(tmp)
        _compile_probe(tmp_dir, cp)

        command = ["java", "-cp", f"{cp}:{tmp_dir}", "PySingleIsoProbe", message["mti"]]
        for key, value in message.items():
            if key == "mti":
                continue
            if not key.isdigit():
                continue
            command.extend([key, value])

        run = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if run.returncode != 0:
            raise RuntimeError(f"ISO send failed:\nSTDOUT:\n{run.stdout}\nSTDERR:\n{run.stderr}")

        print("Switch response:")
        print(run.stdout.strip())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
