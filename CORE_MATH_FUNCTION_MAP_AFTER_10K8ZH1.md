# Core Math Function Map (After 10K8ZH1)

| Function | Inputs | Output | Notes |
|----------|--------|--------|-------|
| `mean` | `list[float]` | `float` | `ValueError` if empty |
| `median` | `list[float]` | `float` | Odd/even length handled |
| `variance` | `list[float]` | `float` | Sample variance (ddof=1) |
| `std_dev` | `list[float]` | `float` | Square root of variance |
| `dot_product` | `list[float]`, `list[float]` | `float` | `ValueError` if length mismatch |
| `weighted_sum` | `list[float]`, `list[float]` | `float` | Weights must sum to 1 |
| `covariance` | `list[float]`, `list[float]` | `float` | Sample covariance |
| `correlation` | `list[float]`, `list[float]` | `float` | `ValueError` if zero variance |
| `correlation_matrix` | `list[list[float]]` | `list[list[float]]` | Symmetric |
| `portfolio_return` | `list[float]`, `list[float]` | `float` | Returns, weights |
| `portfolio_variance` | `list[float]`, `list[list[float]]` | `float` | Weights, covariance matrix |
