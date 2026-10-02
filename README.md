# Acceptance shard repo

This repository exists only to give Vera's nightly staging acceptance suite a
place to create issues, open pull requests and watch the ticket lifecycle run.
Nothing here is a real product.

It is created and seeded by `scripts/ci/ensure_acceptance_repo.py` in the
`golem-works-ai/vera` repo, which runs before every nightly leg. The tree is
checked in there rather than copied from another acceptance repo, so all three
shards start from an identical commit.

`main` is cleaned in place before every run — issues and pull requests are
closed and non-default branches are deleted. Do not keep anything here you
would miss.
