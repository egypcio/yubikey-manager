# -*- coding: utf-8 -*-

from ykman.oath import STEAM_CHAR_TABLE
from .framework import cli_test_suite, yubikey_conditions
import unittest
import contextlib
import io


URI_HOTP_EXAMPLE = (
    "otpauth://hotp/Example:demo@example.com?"
    "secret=JBSWY3DPK5XXE3DEJ5TE6QKUJA======&issuer=Example&counter=1"
)

URI_TOTP_EXAMPLE = (
    "otpauth://totp/ACME%20Co:john.doe@email.com?"
    "secret=HXDMVJECJJWSRB3HWIZR4IFUGFTMXBOZ&issuer=ACME%20Co"
    "&algorithm=SHA1&digits=6&period=30"
)

URI_TOTP_EXAMPLE_B = (
    "otpauth://totp/ACME%20Co:john.doe.b@email.com?"
    "secret=HXDMVJECJJWSRB3HWIZR4IFUGFTMXBOZ&issuer=ACME%20Co"
    "&algorithm=SHA1&digits=6&period=30"
)

URI_TOTP_EXAMPLE_EXTRA_PARAMETER = (
    "otpauth://totp/ACME%20Co:john.doe.extra@email.com?"
    "secret=HXDMVJECJJWSRB3HWIZR4IFUGFTMXBOZ&issuer=ACME%20Co"
    "&algorithm=SHA1&digits=6&period=30&skid=JKS3424d"
)

PASSWORD = "aaaa"


@cli_test_suite
def additional_tests(ykman_cli):
    class TestOATH(unittest.TestCase):
        def setUp(cls):
            ykman_cli("oath", "reset", "-f")

        @classmethod
        def tearDownClass(cls):
            ykman_cli("oath", "reset", "-f")

        def test_oath_info(self):
            output = ykman_cli("oath", "info")
            self.assertIn("version:", output)

        @yubikey_conditions.is_not_fips
        def test_info_does_not_indicate_fips_mode_for_non_fips_key(self):
            info = ykman_cli("oath", "info")
            self.assertNotIn("FIPS:", info)

        def test_oath_add_credential(self):
            ykman_cli("oath", "accounts", "add", "test-name", "abba")
            creds = ykman_cli("oath", "accounts", "list")
            self.assertIn("test-name", creds)

        def test_oath_add_credential_prompt(self):
            ykman_cli("oath", "accounts", "add", "test-name-2", input="abba")
            creds = ykman_cli("oath", "accounts", "list")
            self.assertIn("test-name-2", creds)

        def test_oath_add_credential_with_space(self):
            ykman_cli("oath", "accounts", "add", "test-name-space", "ab ba")
            creds = ykman_cli("oath", "accounts", "list")
            self.assertIn("test-name-space", creds)

        def test_oath_add_credential_alias(self):
            with io.StringIO() as buf:
                with contextlib.redirect_stderr(buf):
                    ykman_cli("oath", "add", "test-name", "abba")
                    ykman_cli("oath", "code", "test-name")
                    creds = ykman_cli("oath", "list")
                    ykman_cli("oath", "delete", "test-name", "-f")
                err = buf.getvalue()
            self.assertIn("test-name", creds)
            self.assertIn("oath accounts add", err)
            self.assertIn("oath accounts code", err)
            self.assertIn("oath accounts list", err)
            self.assertIn("oath accounts delete", err)

        def test_oath_hidden_cred(self):
            ykman_cli("oath", "accounts", "add", "_hidden:name", "abba")
            creds = ykman_cli("oath", "accounts", "code")
            self.assertNotIn("_hidden:name", creds)
            creds = ykman_cli("oath", "accounts", "code", "-H")
            self.assertIn("_hidden:name", creds)

        def test_oath_add_uri_hotp(self):
            ykman_cli("oath", "accounts", "uri", URI_HOTP_EXAMPLE)
            creds = ykman_cli("oath", "accounts", "list")
            self.assertIn("Example:demo", creds)

        def test_oath_add_uri_totp(self):
            ykman_cli("oath", "accounts", "uri", URI_TOTP_EXAMPLE)
            creds = ykman_cli("oath", "accounts", "list")
            self.assertIn("john.doe", creds)

        def test_oath_add_uri_totp_extra_parameter(self):
            ykman_cli("oath", "accounts", "uri", URI_TOTP_EXAMPLE_EXTRA_PARAMETER)
            creds = ykman_cli("oath", "accounts", "list")
            self.assertIn("john.doe.extra", creds)

        def test_oath_add_uri_totp_prompt(self):
            ykman_cli("oath", "accounts", "uri", input=URI_TOTP_EXAMPLE_B)
            creds = ykman_cli("oath", "accounts", "list")
            self.assertIn("john.doe", creds)

        def test_oath_code(self):
            ykman_cli("oath", "accounts", "add", "test-name2", "abba")
            creds = ykman_cli("oath", "accounts", "code")
            self.assertIn("test-name2", creds)

        def test_oath_code_query(self):
            ykman_cli("oath", "accounts", "add", "query-me", "abba")
            creds = ykman_cli("oath", "accounts", "code", "query-me")
            self.assertIn("query-me", creds)

        def test_oath_reset(self):
            output = ykman_cli("oath", "reset", "-f")
            self.assertIn(
                "Success! All OATH credentials have been cleared from the YubiKey",
                output,
            )

        def test_oath_hotp_code(self):
            ykman_cli("oath", "accounts", "add", "-o", "HOTP", "hotp-cred", "abba")
            cred = ykman_cli("oath", "accounts", "code", "hotp-cred")
            self.assertIn("659165", cred)

        def test_oath_totp_steam_code(self):
            ykman_cli(
                "oath", "accounts", "add", "-o", "TOTP", "Steam:steam-cred", "abba"
            )
            cred = ykman_cli("oath", "accounts", "code", "-s", "steam-cred").strip()
            self.assertEqual(5, len(cred), "cred wrong length: %r" % cred)
            self.assertTrue(
                all(c in STEAM_CHAR_TABLE for c in cred),
                "%r contains non-steam characters" % cred,
            )

        def test_oath_delete(self):
            ykman_cli("oath", "accounts", "add", "delete-me", "abba")
            ykman_cli("oath", "accounts", "delete", "delete-me", "-f")
            self.assertNotIn("delete-me", ykman_cli("oath", "accounts", "list"))

        def test_oath_unicode(self):
            ykman_cli("oath", "accounts", "add", "😃", "abba")
            ykman_cli("oath", "accounts", "code")
            ykman_cli("oath", "accounts", "list")
            ykman_cli("oath", "accounts", "delete", "😃", "-f")

        @yubikey_conditions.is_not_fips
        @yubikey_conditions.version_min((4, 3, 1))
        def test_oath_sha512(self):
            ykman_cli(
                "oath", "accounts", "add", "abba", "abba", "--algorithm", "SHA512"
            )
            ykman_cli("oath", "accounts", "delete", "abba", "-f")

        # NEO credential capacity may vary based on configuration
        @yubikey_conditions.version_min((4, 0, 0))
        def test_add_32_creds(self):
            for i in range(32):
                ykman_cli("oath", "accounts", "add", "test" + str(i), "abba")
                output = ykman_cli("oath", "accounts", "list")
                lines = output.strip().split("\n")
                self.assertEqual(len(lines), i + 1)

            with self.assertRaises(SystemExit):
                ykman_cli("oath", "accounts", "add", "testx", "abba")

    @yubikey_conditions.is_fips
    class TestOathFips(unittest.TestCase):
        def setUp(self):
            ykman_cli("oath", "reset", "-f")

        @classmethod
        def tearDownClass(cls):
            ykman_cli("oath", "reset", "-f")

        def test_no_fips_mode_without_password(self):
            output = ykman_cli("oath", "info")
            self.assertIn("FIPS Approved Mode: No", output)

        def test_fips_mode_with_password(self):
            ykman_cli("oath", "access", "change", "-n", PASSWORD)
            output = ykman_cli("oath", "info")
            self.assertIn("FIPS Approved Mode: Yes", output)

        def test_sha512_not_supported(self):
            with self.assertRaises(SystemExit):
                ykman_cli(
                    "oath", "accounts", "add", "abba", "abba", "--algorithm", "SHA512"
                )

    return [
        TestOATH,
        TestOathFips,
    ]
