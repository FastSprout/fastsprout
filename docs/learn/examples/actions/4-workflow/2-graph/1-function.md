# 1. Function

<!-- example-source: examples/actions/04_workflow/02_graph/01_function.py -->

Analyze and summarize one document concurrently, then join the results.
The join action receives a typed ForkResult and returns a DocumentReport.

## Source

```{.python}
--8<-- "examples/actions/04_workflow/02_graph/01_function.py"
```

## Result

```text
analysis=Analysis(words=5) summary=Summary(content='FastSprout makes bac')
```
