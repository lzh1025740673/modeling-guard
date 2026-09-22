# Scope and security limits

Modeling Guard is a workflow check for **cooperative users and trusted experiment scripts**. It is not suitable for executing arbitrary untrusted student submissions or hostile AI-generated code on a teacher's machine.

- Local approval receipts are unsigned and editable. `--teacher` is a label, not identity verification or an access-control boundary. Anyone with write access can forge approval, change code, remove history, or invoke Python directly.
- Snapshotting separates ordinary relative experiment writes from the source project. It does not block absolute paths, network access, filesystem reads, process creation, native extensions, or access to credentials on disk.
- Only a small OS/runtime environment allowlist is inherited; API keys are not deliberately passed. This is a convenience, not a secret-isolation guarantee.
- Time limits terminate the running process and ordinary descendants. POSIX uses a process group; Windows uses `taskkill /T /F` while the parent is alive. Detached processes, children whose Windows parent has already exited, and programs that deliberately escape the process group are not reliably contained. Scripts must join their own children. A leaked log pipe is reported as requiring review; manual process inspection may be necessary.
- The log-size limit bounds the stored console log. The tool does not cap RAM, CPU usage, GPU usage, output-file size, filesystem capacity, network traffic, or financial spending.
- Only declared local files are hashed. Python/interpreter binaries, external packages and imported user-site modules are not locked. Simultaneous adversarial filesystem changes are out of scope.
- Metrics are emitted by the experiment itself. A passing threshold does not detect falsified results, leakage, invalid statistics, wrong units, or unsupported scientific claims.
- Local output and logs can contain private data. Reports have no telemetry or external assets, but **review every file before sharing**. The HTML escapes dynamic text and uses a restrictive content security policy.

Use a teacher-controlled service, separate OS account, container/VM with appropriate policy, or a real execution sandbox when enforcement against an untrusted actor is required. Those integrations are outside v0.1.0.

For public reports, describe the problem using a minimal synthetic example. Do not upload credentials, personal student data, proprietary contest data, or a complete private run directory. For a vulnerability that could expose private data, use GitHub's private vulnerability reporting if enabled; otherwise open a neutral issue requesting a private contact channel without disclosing the exploit or sensitive data.
