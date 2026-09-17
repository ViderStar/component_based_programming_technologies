# Lab 4: Reflection

## Idea

Reflection lets a program look at its own structure at runtime: fields, methods, call-by-name, add a method without editing the class source. In Java: `Class.forName`, `getDeclaredFields`, `Method.invoke`. In Python: `getattr`, `setattr`, `dir`, `inspect`, `type()`.

## Dynamic class

Build `Student` with `name`, `group`, and `greet()` **at runtime**:

```python
Student = type("Student", (object,), {
    "__init__": _init,
    "greet": _greet,
})
```

`type(name, bases, dict)` is how Python builds ordinary `class` blocks. `inspect.signature(student.greet)` still returns `()`.

## Introspection

| Call | Role |
| --- | --- |
| `getattr(obj, "greet")` | attribute by string |
| `setattr` | write attribute or method |
| `hasattr` | existence check |
| `dir` | name list |
| `inspect.signature` | signature |
| `inspect.getmembers` | name/value pairs |

The GUI shows a member tree. Calls go through `getattr(student, method_name)(*args)`.

## Runtime methods

- on an **instance**: `types.MethodType(func, obj)`
- on the **class**: `setattr(Student, "shout", lambda self: ...)`

That is “add a new method at run-time and run it”.

## Java → Python

The handout: send a method from a Java program to a Python script.

Protocol: one JSON line `{"method": "greet", "args": []}` over TCP. The Python bridge does `getattr(student, method)(*args)` and replies `{"ok": true, "result": "..."}`. `MethodSender.java` is a plain `Socket`. Same idea as Lab 2 XML-RPC, different language on the other side.

## Annotations / tests

The older Java lab stored expected output in an annotation. Here:

```python
@expected(1, "Hie, Dear")
def get_str(self, index: int) -> str: ...
```

Reflection finds `_expected`, calls the method, compares. Two methods, as required.

## `__new__` without `__init__`

The lecture shows `__new__` plus a manual `__init__`. Serializers and ORMs do this. The stand uses `type()` plus a normal constructor.

## Links

- pickle (Lab 1) restores a class by name;
- XML-RPC (Lab 2) picks a method by `methodName`;
- GUI (Lab 3) binds handlers by tool id — call-by-name again.
