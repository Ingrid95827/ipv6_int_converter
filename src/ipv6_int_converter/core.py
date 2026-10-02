"""Convert between the colon-hex string form of an IPv6 address and its
packed 128-bit integer representation.

Design decisions, stated plainly so the tests can pin them down:

* The integer is treated as a *non-negative* Python ``int`` of arbitrary
  precision, restricted to the range ``[0, 2**128 - 1]``. We deliberately do
  *not* return a fixed-width ``bytes`` object, because the brief asks for a
  "128-bit integer", and Python's ``int`` is the natural carrier for that.
* Parsing uses the standard library's :func:`ipaddress.IPv6Address`, which
  normalises embedded IPv4-mapped forms, leading/trailing ``::`` collapses,
  and case. Output therefore goes through the same type to guarantee
  round-trip canonicalisation rather than a hand-rolled formatter that
  could drift from RFC 5952.
* We reject zone IDs (``fe80::1%eth0``). ``ipaddress`` accepts them on
  str input but they are not part of the 128-bit address itself; carrying
  them would break the integer round-trip. A dedicated error type makes
  that failure mode explicit instead of smuggling it through ``ValueError``.
"""

from __future__ import annotations

import ipaddress


class Ip6Error(ValueError):
    """Raised when a value is not a valid IPv6 address or 128-bit integer.

    Subclassing :class:`ValueError` keeps the library ergonomic for callers
    who already catch ``ValueError`` from :mod:`ipaddress`, while still
    letting library users target *only* this module's failures.
    """


_MASK = (1 << 128) - 1


def ip_to_int(address: str) -> int:
    """Return the 128-bit integer for ``address``.

    ``address`` must be a colon-hex IPv6 string with no zone identifier.
    Embedded IPv4 dotted-quad tails (``::ffff:192.0.2.1``) are accepted and
    normalised by :mod:`ipaddress` before conversion, because they denote
    the same 128-bit value.

    Raises :class:`Ip6Error` for malformed input, IPv4-only input, or input
    carrying a zone ID.
    """
    if not isinstance(address, str):
        raise Ip6Error(f"address must be str, got {type(address).__name__}")

    # ``ipaddress`` silently strips a trailing ``%zone`` and stores it on the
    # object; for our purposes a zone makes the integer round-trip lossy, so
    # we reject it up front by looking at the raw string.
    if "%" in address:
        raise Ip6Error("zone identifiers are not supported")

    try:
        parsed = ipaddress.IPv6Address(address)
    except ipaddress.AddressValueError as exc:
        raise Ip6Error(str(exc)) from exc

    # ``int()`` on an ``IPv6Address`` yields the unsigned 128-bit value
    # directly; no manual packing is required.
    return int(parsed)


def int_to_ip(value: int) -> str:
    """Return the canonical colon-hex IPv6 string for ``value``.

    ``value`` must be an integer in ``[0, 2**128 - 1]``. Booleans are rejected
    even though ``bool`` is a subclass of ``int``, because ``True``/``False``
    as an address is almost always a caller bug rather than intent.

    The returned string is the RFC 5952 compressed form produced by
    :mod:`ipaddress`, which guarantees stable, comparable output.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise Ip6Error(f"value must be int, got {type(value).__name__}")
    if value < 0 or value > _MASK:
        raise Ip6Error(f"value out of range: {value}")

    # Constructing from an int bypasses the string parser entirely, so we
    # only need to guard the range, which we did above.
    return str(ipaddress.IPv6Address(value))
