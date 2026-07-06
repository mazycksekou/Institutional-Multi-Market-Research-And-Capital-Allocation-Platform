# Market Profile Implementation Plan

This document summarizes the first reusable market profile framework implementation.

## What was created

- a canonical Market Profile Contract
- a lightweight Market Profile Registry
- reusable market profile definitions for:
  - Sports
  - Prediction Markets
  - Options / 0DTE
  - NFL as the first Sports instance

## What the framework is for

The framework gives the repository one reusable contract shape for future market families.

It is intended to support:

- storage design
- feature design
- backtest design
- research design
- Streamlit design
- Worldview compatibility

## What it does not do

It does not:

- fetch data
- call providers
- build features
- train models
- run backtests
- render dashboards

## Next recommended use

The next task should build the first market-specific research and storage slice on top of this framework, starting with the NFL sports profile.
