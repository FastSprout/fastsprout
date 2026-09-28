Pass an `EventBus` into `DataR` to receive typed persistence events. The handler subscribes to `CreateEvent[HeroEntity]`; creating a hero causes that handler to run, and the example waits for its event state.

## Result

The handler receives a `CreateEvent[HeroEntity]` for Batman:

```text
Create Event: Batman
```
