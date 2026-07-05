# Brokerage Disabled Behavior After 10K8ZIB

submit_order_disabled() always raises DisabledBrokerageError or
DisabledExecutionError.

The boundary:
- does not submit orders
- does not create broker accounts
- does not read credentials
- does not open network connections
- does not write externally

No paper-only canonical path exists.
