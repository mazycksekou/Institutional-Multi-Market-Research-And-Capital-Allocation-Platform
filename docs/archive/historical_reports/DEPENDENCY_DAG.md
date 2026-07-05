# Dependency DAG

| from | to | count |
| --- | --- | --- |
| tests | src.services | 267 |
| src.market_intelligence | src.market_intelligence | 197 |
| tests | src.brokerage | 143 |
| src.analytics | src.market_intelligence | 111 |
| src.brokerage | src.brokerage | 99 |
| src.providers | src.providers | 69 |
| src.connectors | src.connectors | 67 |
| tests | src.providers | 67 |
| tests | src.connectors | 67 |
| src.analytics | src.analytics | 66 |
| tests | src.market_intelligence | 63 |
| tests | tests | 61 |
| tests | src.analytics | 58 |
| src.core | src.core | 46 |
| src.services | src.services | 43 |
| src.brokerage.__init__.py | src.brokerage | 38 |
| tests | src.core | 38 |
| tests | src.data.__init__.py | 31 |
| root | src.api | 27 |
| src.market_intelligence | src.security | 23 |
| src.analytics | src.services | 22 |
| src.services | src.analytics | 22 |
| src.services | src.core | 21 |
| src.services | src.providers | 20 |
| src.market_intelligence.__init__.py | src.market_intelligence | 19 |
| src.analytics | src.security | 16 |
| src.backtesting | src.backtesting | 16 |
| src.market_intelligence | src.services | 16 |
| src.providers.__init__.py | src.providers | 15 |
| src.core | src.security | 14 |

