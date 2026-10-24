# Security Policy

## Supported version

Security fixes are currently applied to the latest `0.x` release.

## Reporting

Do not open a public issue for a vulnerability that could expose credentials, private research documents, or repository tokens. Contact the project maintainer privately and include reproduction steps, affected files, and expected impact.

## Data handling

The baseline application processes uploaded PDFs in memory. Optional GitHub tokens are used only for API requests and are not intentionally written into generated reports. Users should still avoid uploading confidential manuscripts to public deployments they do not control.
