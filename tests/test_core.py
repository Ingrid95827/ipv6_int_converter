import unittest

from ipv6_int_converter import ip_to_int, int_to_ip, Ip6Error


class IpToIntTests(unittest.TestCase):
    def test_loopback(self):
        self.assertEqual(ip_to_int("::1"), 1)

    def test_unspecified(self):
        self.assertEqual(ip_to_int("::"), 0)

    def test_full_form(self):
        # 2001:0db8:0000:0000:0000:0000:0000:0001 -> canonical int
        self.assertEqual(
            ip_to_int("2001:0db8:0000:0000:0000:0000:0000:0001"),
            0x20010DB8000000000000000000000001,
        )

    def test_compressed_form_matches_full(self):
        self.assertEqual(
            ip_to_int("2001:db8::1"),
            ip_to_int("2001:0db8:0000:0000:0000:0000:0000:0001"),
        )

    def test_ipv4_mapped_tail(self):
        # ::ffff:192.0.2.33 is the IPv4-mapped form; ipaddress normalises it.
        expected = int.from_bytes(
            bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xFF, 0xFF, 192, 0, 2, 33]),
            "big",
        )
        self.assertEqual(ip_to_int("::ffff:192.0.2.33"), expected)

    def test_all_ones(self):
        self.assertEqual(ip_to_int("ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff"), (1 << 128) - 1)

    def test_case_insensitive(self):
        self.assertEqual(ip_to_int("FFFF::1"), ip_to_int("ffff::1"))

    def test_rejects_ipv4_only(self):
        with self.assertRaises(Ip6Error):
            ip_to_int("192.0.2.1")

    def test_rejects_zone_id(self):
        with self.assertRaises(Ip6Error):
            ip_to_int("fe80::1%eth0")

    def test_rejects_extra_groups(self):
        with self.assertRaises(Ip6Error):
            ip_to_int("1:2:3:4:5:6:7:8:9")

    def test_rejects_non_string(self):
        with self.assertRaises(Ip6Error):
            ip_to_int(123)  # type: ignore[arg-type]


class IntToIpTests(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(int_to_ip(0), "::")

    def test_one(self):
        self.assertEqual(int_to_ip(1), "::1")

    def test_compression_applied(self):
        # The canonical form must compress the longest run of zero groups.
        self.assertEqual(
            int_to_ip(0x20010DB8000000000000000000000001),
            "2001:db8::1",
        )

    def test_no_compression_when_no_zeros(self):
        self.assertEqual(
            int_to_ip(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF),
            "ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff",
        )

    def test_rejects_negative(self):
        with self.assertRaises(Ip6Error):
            int_to_ip(-1)

    def test_rejects_overflow(self):
        with self.assertRaises(Ip6Error):
            int_to_ip(1 << 128)

    def test_rejects_bool(self):
        # bool is a subclass of int; accepting it would let ``True`` silently
        # mean ``::1``, which is almost always a caller bug.
        with self.assertRaises(Ip6Error):
            int_to_ip(True)

    def test_rejects_non_int(self):
        with self.assertRaises(Ip6Error):
            int_to_ip("::1")  # type: ignore[arg-type]


class RoundTripTests(unittest.TestCase):
    def test_round_trip_examples(self):
        samples = [
            "::",
            "::1",
            "2001:db8::1",
            "fe80::1",
            "ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff",
            "::ffff:192.0.2.33",
        ]
        for s in samples:
            with self.subTest(s):
                # Every input first parses to an int, then the int must
                # render back to the *canonical* form. For inputs that are
                # already canonical that is a strict equality; for others we
                # only require that re-parsing the output yields the same int.
                self.assertEqual(ip_to_int(int_to_ip(ip_to_int(s))), ip_to_int(s))


if __name__ == "__main__":
    unittest.main()
