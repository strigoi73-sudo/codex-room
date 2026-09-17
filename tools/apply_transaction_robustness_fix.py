from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected exactly one match, found {count}: {old[:120]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def update_development_control() -> None:
    path = "docs/project/06_DEVELOPMENT_CONTROL.md"
    replace_once(
        path,
        '- **What just changed?** **D-034 activation follow-through is complete.** After PR #107 activated v2 + `assignment_thread`, the local checkout fast-forwarded to canonical `main`, **77 legacy Rooms were deleted offline with foreign-key checks**, Room workspaces/bindings were cleared, and one fresh production smoke Room (`room_e150b0dce6504d979183609ab0d5d08d`) completed through the v2 transaction path with one C Assignment, zero Joins, one `COMPLETE`, and one model execution. See E-121 and E-122.\n',
        '- **What just changed?** Ordinary Common Cause use exposed one bounded post-I-015 transaction robustness defect before implementation began. PR #108 repairs the EVIDENCE/HISTORY contract mismatch and makes the existing one-shot validation retry independent of successful Assignment continuations. Exact Linux full-suite verification passed **421 tests, 2 warnings**; Windows transaction/source verification passed **43 tests** on identical production bytes. See E-123.\n',
    )
    replace_once(
        path,
        '- **What is next?** **Return to ordinary Codex Room development/use.** I-015 is closed. Do not launch additional v2 compatibility/migration work or broad validation unless ordinary use exposes a concrete defect.\n',
        '- **What is next?** **Resume ordinary Codex Room development/use, including the interrupted Common Cause implementation.** I-015 remains closed. Do not launch broader v2 compatibility/migration or validation work unless ordinary use exposes another concrete defect.\n',
    )
    replace_once(
        path,
        '**Evidence:** E-092 through E-122  \n**Scope:** [CORE]. Legacy Rooms were deleted rather than migrated; no compatibility migration remains.\n',
        '**Evidence:** E-092 through E-123\n**Scope:** [CORE]. Legacy Rooms were deleted rather than migrated; no compatibility migration remains.\n\n**Post-close ordinary-use repair — COMPLETE / IMPLEMENTED / VERIFIED (2026-09-16):** The Common Cause implementation Round exposed a residual transaction-contract/retry edge after I-015 closeout: EVIDENCE path semantics were not explicit enough for the agent-facing contract, HISTORY schema bounds were incompletely advertised, and a malformed decision after a successful continuation could exhaust the Assignment retry budget. PR #108 applies the bounded repair and adds exact regression coverage. This is ordinary-use defect repair under the existing D-031/D-033/D-034 architecture, not a reopening of I-015 or a new broad validation program. See E-123.\n',
    )


def update_architecture() -> None:
    path = "docs/project/04_ARCHITECTURE_AND_CURRENT_STATE.md"
    replace_once(path, '**Last synthesized:** 2026-09-14  \n', '**Last synthesized:** 2026-09-16\n')
    marker = '**Stage-D D-N4 remediation status — IMPLEMENTED / VERIFIED / MERGED (2026-09-16):** PR #104 merged the structured-EVIDENCE contract/telemetry repair, and the repository-standard `verify-fast.cmd` then passed on exact code-bearing canonical-main commit `668ef98253c5bd1387eefb1b71f99ed38fd8b53c`: Linux/Python 3.12 focused core **45 passed, 2 warnings**; Windows focused portability **118 passed**; browser transcript stability **3 passed**; total verifier time **74.7 seconds** with all phases exit code 0 and a clean tracked tree. The repair aligns provider/runtime path validation, states CORE path semantics, preserves invalid-decision usage/activity/economics, and supplies one-shot retry feedback without stale leakage. E-108 records implementation/focused evidence; E-110 records merged-tree verification.\n'
    addition = marker + '\n**Post-activation ordinary-use transaction robustness repair — IMPLEMENTED / VERIFIED — 2026-09-16:** A Common Cause implementation Round exposed residual contract/retry edge cases after D-N4: C supplied an absolute Windows workspace path to `EVIDENCE` because the agent-facing contract did not state source-relative path semantics, then emitted `HISTORY max_results=12` because the provider JSON schema omitted the Pydantic maximum of 10. The second malformed decision became terminal because Assignment retry eligibility counted every prior execution, including successful `EVIDENCE` / `HISTORY` continuations. PR #108 aligns provider schema bounds with runtime bounds, states that EVIDENCE paths are normalized source-relative forward-slash paths (`.` may select a workspace/Room root but not the CORE root), states HISTORY\'s 1–10 / maximum-four request contract, and makes the single corrective retry budget depend on prior failed executions rather than successful continuations. The hidden aggregate HISTORY request-sum validator was removed; retained prior-Round context remains mechanically capped at 20 event IDs by the selector. Regression coverage includes the exact successful-EVIDENCE → malformed-decision → retry → valid-completion path. See E-123.\n'
    replace_once(path, marker, addition)


def update_evidence_register() -> None:
    path = Path("docs/project/07_EVIDENCE_REGISTER.md")
    text = path.read_text(encoding="utf-8")
    heading = "### E-123 — Ordinary-use transaction contract/retry repair"
    if heading in text:
        raise RuntimeError("E-123 already exists")
    entry = r'''
### E-123 — Ordinary-use transaction contract/retry repair
**Date:** 2026-09-16
**Kind:** Naturalistic production defect + bounded CORE repair

A Common Cause implementation Round in Room `room_975e0a78e6b040d5bf26d460d577e312` exposed a residual work-model-v2 robustness defect before any game implementation began.

Observed sequence from `Three-Player-Strategy-Game (2).json`:

- C requested workspace `EVIDENCE` with an absolute Windows shared-workspace path; the source inspector correctly rejected it because paths are normalized relative paths.
- On the resumed Assignment, C requested `HISTORY` with `max_results=12`. The provider-facing transaction JSON schema did not advertise the runtime Pydantic maximum of 10, so a provider decision could satisfy the presented schema and still fail internal validation.
- Because the Assignment had already completed one valid EVIDENCE continuation, retry eligibility counted two total Assignment executions and made this malformed decision terminal. The Round closed `transaction_failed`.
- The two C executions consumed **44,496 execution tokens** (21,511 + 22,985) without implementation work beginning.

Repair:

- the transaction provider schema now mirrors the relevant Pydantic bounds for delegation instructions, EVIDENCE READ/SEARCH/FIND limits, and HISTORY `max_results`;
- EVIDENCE agent guidance now states source-relative normalized forward-slash paths, forbids absolute filesystem paths, and states `.` root semantics;
- HISTORY guidance states 1–10 results per request and at most four requests;
- the hidden aggregate requested-result validator was removed while actual retained prior-Round context remains mechanically capped at 20 selected event IDs;
- one corrective Assignment retry now depends on the count of prior failed executions, so successful EVIDENCE/HISTORY continuations do not consume the retry budget;
- regression coverage reproduces successful EVIDENCE → malformed decision → feedback retry → valid completion.

Verification:

- code-bearing repair commit `4c5644fb2273dfe8c9a3d2de809423bb5e988984`;
- exact post-regression-alignment head `9022e4ab4320de96ffa27d1c2ee9fd2673435a47` passed Linux/Python 3.12 full suite **421 passed, 2 warnings** and `git diff --check`;
- Windows focused transaction/source tests passed **43 tests** on `a04edb2a831643f8cfb125a7a87d6e7f61ee1be0`, whose production bytes match `9022e4ab...`; the later difference is the aligned history-validation regression test.

**Assessment:** OBSERVED ISSUE → IMPLEMENTED / VERIFIED bounded repair. This is post-I-015 ordinary-use defect repair, not a reopening of broad v2 validation.
'''
    path.write_text(text.rstrip() + "\n\n" + entry.strip() + "\n", encoding="utf-8")


def main() -> None:
    update_development_control()
    update_architecture()
    update_evidence_register()
    print("Updated owning project documents for E-123.")


if __name__ == "__main__":
    main()
