"""Local file CLI; no transport or server entry point."""

import argparse
import os
import sys

from .contracts import INPUT_BYTES, Invalid, parse
from .model import evaluate
from .report import encode, write_fresh


def _silence_failed_stream(stream):
    """Prevent a failed standard stream's buffered shutdown retry.

    Only the failed process's standard descriptor is redirected to the OS null sink.
    No representation is opened. Host descriptor failures remain outside the boundary.
    """
    descriptor, silenced = None, False
    try:
        descriptor = os.open(os.devnull, os.O_WRONLY)
        os.dup2(descriptor, stream.fileno())
        silenced = True
    except (OSError, ValueError, AttributeError, TypeError):
        pass
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                silenced = False
    if not silenced:
        # Also handle unusable host descriptors/custom test sinks without a second flush.
        if sys.stdout is stream:
            sys.stdout = None
        if sys.stderr is stream:
            sys.stderr = None
    return silenced


def _silence_failed_stdout():
    return _silence_failed_stream(sys.stdout)


def _stdout(payload):
    try:
        written = sys.stdout.buffer.write(payload)
        if type(written) is not int or written != len(payload):
            raise OSError("SHORT_STDOUT_WRITE")
        sys.stdout.buffer.flush()
    except (OSError, ValueError):
        if not _silence_failed_stdout():
            raise Invalid("STDOUT_WRITE_AND_SILENCE_FAILED") from None
        raise


def _diagnostic(code):
    """One bounded fixed-code attempt; failed stderr never replaces the chosen exit."""
    stream = sys.stderr
    message = "rangelab: " + code + "\n"
    try:
        written = stream.write(message)
        if type(written) is not int or written != len(message):
            raise OSError("SHORT_DIAGNOSTIC_WRITE")
        stream.flush()
    except (OSError, ValueError, AttributeError):
        _silence_failed_stream(stream)


class _Arguments(Exception):
    pass


class _HelpComplete(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, _message):
        # Do not reproduce supplied argument values or native error text.
        raise _Arguments()

    def _print_message(self, message, file=None):
        # Only help is printed: error() above emits no argparse usage/argument text.
        if message:
            _stdout(message.encode("utf-8"))

    def exit(self, status=0, message=None):
        raise _HelpComplete()


def main(argv=None):
    parser = _Parser(prog="rangelab", description="Offline normalized byte-range teaching model")
    parser.add_argument("input")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--output", help="New file only; existing files are rejected")
    try:
        args = parser.parse_args(argv)
        if not args.input or "\x00" in args.input:
            raise Invalid("INVALID_INPUT_PATH")
        if args.output is not None and (not args.output or "\x00" in args.output):
            raise Invalid("INVALID_OUTPUT_PATH")
        if args.output is not None and os.path.normcase(os.path.realpath(args.input)) == os.path.normcase(os.path.realpath(args.output)):
            raise Invalid("INPUT_OUTPUT_ALIAS")
        with open(args.input, "rb") as source:
            raw = source.read(INPUT_BYTES + 1)
        report = evaluate(parse(raw))
        payload = encode(report, args.format)
        if args.output is not None:
            write_fresh(args.output, payload)
        else:
            _stdout(payload)
        return 2 if any(item["status"] == "UNSUPPORTED" for item in report["results"]) else 0
    except _HelpComplete:
        return 0
    except _Arguments:
        _diagnostic("ARGUMENT_ERROR")
        return 2
    except Invalid as exc:
        _diagnostic(str(exc))
    except (OSError, ValueError):
        _diagnostic("IO_ERROR")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

