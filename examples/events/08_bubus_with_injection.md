Wrap a native Bubus bus with `InMemoryBroker`, then register that `EventBus` as a `Depends` override. The decorators resolve the same bus through dependency injection. The override is removed after the example finishes.

## Result


```text
Hello, FastSprout!
```
