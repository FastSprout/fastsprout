`JoinedStream` combines async streams with an inner join. The plan is lazy: it starts reading the streams only when `to_list()` is called. Each result is a typed `(Order, Customer, Product)` tuple.

## Result

Only orders with matching customer and product rows appear:

```text
[(1, 'Ada', 'Tea'), (2, 'Ada', 'Coffee')]
```

Order 3 has no matching customer and is omitted.
