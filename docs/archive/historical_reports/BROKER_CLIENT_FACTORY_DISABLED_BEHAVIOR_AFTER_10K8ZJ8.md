# Broker Client Factory Disabled Behavior After 10K8ZJ8

The broker client factory is a disabled scaffold.

Rules:

- `create_broker_client_disabled()` always raises `DisabledBrokerClientError`.
- create_broker_client_disabled() always raises DisabledBrokerClientError.
- The broker client factory is still approval-gated only in metadata.
- No live client is created.
- No SDK or network behavior is activated.
