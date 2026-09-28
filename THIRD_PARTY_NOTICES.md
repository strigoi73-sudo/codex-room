# Third-Party Notices

Codex Room includes or references third-party material. The root MIT license applies to original Codex Room work and does not replace the licenses or notices that govern third-party material.

## CooperBench benchmark material

OUB v2 contains selected feature specifications and test patches copied from:

- **Project:** CooperBench
- **Repository:** `cooperbench/CooperBench`
- **Frozen revision:** `63b9d44d9f39a02fccf5bf0052db48a917a011fd`
- **Upstream license declaration at that revision:** MIT (`pyproject.toml` declares `license = {text = "MIT"}`)

The copied material is under `benchmarks/oub/v2/tasks/` and `benchmarks/oub/v2/grading/`. The benchmark manifest and sample files preserve exact source identities and upstream revision information.

CooperBench authors listed in the frozen upstream project metadata include Arpandeep Khatua, Hao Zhu, Peter Tran, Arya Prabhudesai, Frederic Sadrieh, Johann K. Lieberwirth, Xinkai Yu, Yicheng Fu, Michael J. Ryan, Jiaxin Pei, and Diyi Yang.

## Upstream repositories used by OUB v2

OUB v2 materializes exact commits from external projects during benchmark execution. Those repositories are not vendored wholesale into Codex Room.

- **LlamaIndex** — `run-llama/llama_index`, frozen task base `5eca4973cef04eca5d817d3e1515c8cbe7d1cf9e`; upstream license: MIT.
- **Typst** — `typst/typst`, frozen task base `b8034a343831e8609aec2ec81eb7eeda57aa5d81`; upstream license: Apache License 2.0.
- **dirty-equals** — `samuelcolvin/dirty-equals`, frozen task base `593bcccf738ab8b724d7cb860881d74344171f5f`; upstream license: MIT.

Where a benchmark patch contains material derived from one of these upstream projects, the applicable upstream terms continue to apply.

## Runtime and package dependencies

Python packages and external runtimes used by Codex Room are separate works distributed under their own licenses. Installing dependencies through `pyproject.toml`, `constraints-test.txt`, Python packaging tools, Codex, Rust, WSL, or other external tooling does not relicense those dependencies under the Codex Room MIT license.

This notice is informational and is not a substitute for the license text distributed by each upstream project.
