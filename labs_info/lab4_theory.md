# ЛР №4: Рефлексия

## Введение

Рефлексия — способность программы смотреть на свою структуру во время выполнения: какие есть поля и методы, как их вызвать по имени, как добавить новый метод, не переписывая класс заранее. В Java это `Class.forName`, `getDeclaredFields`, `Method.invoke`. В Python — `getattr`, `setattr`, `dir`, `inspect`, `type()`.

## Динамический класс

Задание: создать `Student` с полями `name`, `group` и методом `greet()` **динамически**.

```python
Student = type("Student", (object,), {
    "__init__": _init,
    "greet": _greet,
})
```

`type(name, bases, dict)` — тот же механизм, которым Python создаёт обычные `class` блоки. Рефлексия работает и с такими классами: `inspect.signature(student.greet)` возвращает `()`.

## Интроспекция

| Функция | Назначение |
| --- | --- |
| `getattr(obj, "greet")` | достать атрибут по строке |
| `setattr` | записать атрибут или метод |
| `hasattr` | проверить наличие |
| `dir` | список имён |
| `inspect.signature` | сигнатура |
| `inspect.getmembers` | пары имя/значение |

GUI показывает дерево членов. Вызов идёт через `getattr(student, method_name)(*args)`.

## Методы в runtime

- на **экземпляр**: `types.MethodType(func, obj)` — bound method только у этого объекта;
- на **класс**: `setattr(Student, "shout", lambda self: ...)` — появится у всех экземпляров.

Так демонстрируется пункт «add new method in run-time and running it».

## Java → Python

В методичке: «Show Java-Python interaction by sending method from Java program to python script».

Протокол: одна JSON-строка `{"method": "greet", "args": []}` по TCP. Python-мост делает `getattr(student, method)(*args)` и отвечает `{"ok": true, "result": "..."}`. Java-клиент `MethodSender.java` — обычный `Socket`, без библиотек. Это тот же приём, что XML-RPC в ЛР2, только имя метода приходит от другой JVM.

## Аннотации и тесты

Старая методичка на Java предлагала записать в аннотации ожидаемый выход и прогнать несколько методов. В Python это декоратор:

```python
@expected(1, "Hie, Dear")
def get_str(self, index: int) -> str: ...
```

Рефлексия находит методы с атрибутом `_expected`, вызывает их и сравнивает результат. Два метода — как требовалось («более одного метода»).

## Создание объекта без конструктора

В лекции показаны `__new__` + ручной `__init__`. Это полезно понимать: фабрики, pickle и ORM так обходят обычный конструктор. В стенде основной путь — `type()` + обычный `__init__`.

## Связь с другими работами

- pickle (ЛР1) восстанавливает класс по имени — это рефлексия импорта;
- XML-RPC (ЛР2) выбирает метод по строке `methodName`;
- GUI (ЛР3) биндит обработчики по id инструментов — родственная идея «вызвать по имени».
