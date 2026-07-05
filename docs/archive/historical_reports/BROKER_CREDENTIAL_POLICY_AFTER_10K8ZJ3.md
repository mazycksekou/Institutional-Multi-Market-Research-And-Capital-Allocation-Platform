# Broker Credential Policy After 10K8ZJ3

- `BrokerCredentialDescriptor` is metadata only.
- `BrokerCredentialPolicy` describes future credential needs without reading env vars.
- `validate_broker_credentials_disabled()` always raises `DisabledBrokerCredentialError`.
- `import_time_reads_blocked` remains `True`.
- `live_trading_allowed` remains `False`.
