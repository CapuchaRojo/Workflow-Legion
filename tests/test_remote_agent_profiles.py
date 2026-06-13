import unittest

from backend.app.services.remote_agent_profiles import (
    PROOF_STATUS_VALIDATED,
    REMOTE_AGENT_PROFILES,
)


EXPECTED_ROLES = {
    "triage",
    "threat_intel",
    "forensics",
    "compliance",
    "commander",
}


class RemoteAgentProfilesTest(unittest.TestCase):
    def test_all_five_roles_exist(self) -> None:
        self.assertEqual(set(REMOTE_AGENT_PROFILES), EXPECTED_ROLES)

    def test_profiles_have_required_setup_fields(self) -> None:
        for role_key, profile in REMOTE_AGENT_PROFILES.items():
            with self.subTest(role_key=role_key):
                self.assertEqual(profile.role_key, role_key)
                self.assertTrue(profile.display_name.strip())
                self.assertTrue(profile.suggested_band_handle.strip())
                self.assertTrue(profile.description.strip())
                self.assertTrue(profile.tags)
                self.assertTrue(profile.runtime_instructions.strip())

    def test_handles_do_not_include_band_mention_prefix(self) -> None:
        for role_key, profile in REMOTE_AGENT_PROFILES.items():
            with self.subTest(role_key=role_key):
                self.assertFalse(profile.suggested_band_handle.startswith("@"))

    def test_handoff_chain_is_explicit(self) -> None:
        self.assertEqual(
            REMOTE_AGENT_PROFILES["triage"].handoff_targets,
            ("threat_intel", "forensics"),
        )
        self.assertEqual(
            REMOTE_AGENT_PROFILES["threat_intel"].handoff_targets,
            ("compliance",),
        )
        self.assertEqual(
            REMOTE_AGENT_PROFILES["forensics"].handoff_targets,
            ("compliance",),
        )
        self.assertEqual(
            REMOTE_AGENT_PROFILES["compliance"].handoff_targets,
            ("commander",),
        )
        self.assertEqual(
            REMOTE_AGENT_PROFILES["commander"].handoff_targets,
            ("final_decision",),
        )

    def test_proof_status_boundary_is_honest(self) -> None:
        for role_key in EXPECTED_ROLES:
            with self.subTest(role_key=role_key):
                self.assertEqual(
                    REMOTE_AGENT_PROFILES[role_key].proof_status,
                    PROOF_STATUS_VALIDATED,
                )

    def test_runtime_instructions_keep_demo_safe_boundaries(self) -> None:
        for role_key, profile in REMOTE_AGENT_PROFILES.items():
            with self.subTest(role_key=role_key):
                instructions = profile.runtime_instructions.lower()
                self.assertIn("scope:", instructions)
                self.assertIn("band as the visible coordination fabric", instructions)
                self.assertIn("backend owns deterministic workflow runtime", instructions)
                self.assertIn("provided evidence", instructions)
                self.assertIn(
                    "do not make unsupported breach, legal, or medical claims",
                    instructions,
                )
                self.assertIn("handoff target:", instructions)

    def test_runtime_instructions_name_their_handoff_targets(self) -> None:
        expected_phrases = {
            "triage": ("threat intel", "forensics"),
            "threat_intel": ("compliance",),
            "forensics": ("compliance",),
            "compliance": ("incident commander",),
            "commander": ("final_decision",),
        }

        for role_key, target_phrases in expected_phrases.items():
            with self.subTest(role_key=role_key):
                instructions = REMOTE_AGENT_PROFILES[
                    role_key
                ].runtime_instructions.lower()
                for target_phrase in target_phrases:
                    self.assertIn(target_phrase, instructions)


if __name__ == "__main__":
    unittest.main()
