`BaseAction[Input, Output]` describes one asynchronous result. Both a callable class and an `async def` function are recognized as actions; the example calls each with the same input schema.

## Result

Both forms return the same typed output:

```text
message='hello, world'
message='hello, world'
```
