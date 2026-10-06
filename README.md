# IPv6 Int Converter

Convert IPv6 addresses between colon-hex string and packed 128-bit integer
representations. Standard library only, no dependencies.

```python
from ipv6_int_converter import ip_to_int, int_to_ip, Ip6Error

ip_to_int("2001:db8::1")        # -> 42540488161975842760550356425300246529
int_to_ip(42540488161975842760550356425300246529)  # -> "2001:db8::1"
```

## Why

Storage and comparison of IPv6 addresses is awkward: the string form is
variable-length and human-oriented, while databases and hash tables prefer a
fixed-width numeric key. This library gives you a single canonical integer for
each address so equality checks and range queries become integer arithmetic.

The trade-off is that we lean on `ipaddress.IPv6Address` for both parsing and
formatting. That keeps the code small and correct against RFC 5952, at the cost
of accepting whatever normalisation rules Python's stdlib chooses to apply.
If you need a non-canonical output form (e.g. fully expanded zeros), this
library is the wrong tool.

## Edge cases

* Embedded IPv4-mapped tails (`::ffff:192.0.2.33`) are accepted and treated as
  the 128-bit value they denote.
* Zone identifiers (`fe80::1%eth0`) are **rejected** with `Ip6Error`. They are
  not part of the 128-bit address and would make the integer round-trip lossy.
* `int_to_ip(True)` raises `Ip6Error`; `bool` is a subclass of `int` but passing
  one is almost always a bug.
* Input integers must be in `[0, 2**128 - 1]`. Negative values and values that
  exceed 128 bits raise `Ip6Error`.

The exported names are exactly: `ip_to_int`, `int_to_ip`, `Ip6Error`.

## Tests

```
PYTHONPATH=src python -m unittest discover -s tests
```

## Design notes

The window stores values eagerly rather than keeping running aggregates. Running
sums drift with floating point over long streams, and recomputing from a small
buffer is cheap enough that the drift is not worth the speed.

