py := '3.13'

update: lock-upgrade pre-commit-autoupdate gha build test

lock-upgrade:
    uv lock --upgrade

pre-commit-autoupdate:
    uvx --python={{py}} --with pre-commit-uv pre-commit autoupdate

gha:
    uvx --python={{py}} gha-update

build:
    uv build

test:
    uvx --python={{py}} --with=tox-uv tox run-parallel
