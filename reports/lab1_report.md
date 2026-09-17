# Lab 1 report

**Institution**  
Belarusian State University of Informatics and Radioelectronics

Faculty of Computer Systems and Networks (FCSN), POIT, group PI

**Lab 1 report**  
Course: Component-Based Programming Technologies

**Topic:** object serialization and deserialization (pickle, JSON, network, WebP/base64)

| | |
| --- | --- |
| Author | Artsem Lebiadzevich, year-2 MSc, FCSN, POIT, PI |
| Supervisor | Oleg German, PhD, Associate Professor |
| Minsk | 2026 |

---

## 1. Goal

Serialize and deserialize Python objects: files, TCP, a visual form snapshot. Extra: ship a WebP image as raw bytes (pickle) and as base64 (JSON).

## 2. Work done

1. `Student` with name, group, faculty, optional `Photo`.
2. Object built in GUI/CLI; photo from `assets/samples/avatar.webp`.
3. Written to `artifacts/student.pkl` and `artifacts/student.json`.
4. Read by another process: `python -m lab1.reader`.
5. TCP server/client with a 4-byte length prefix (not `recv(1024)`).
6. GUI form snapshot via `GuiFormState.to_dict`.
7. Steps 1–6 for pickle and JSON separately.

Code: [`lab1/`](../lab1/). Theory: [`labs_info/lab1_theory.md`](../labs_info/lab1_theory.md).

## 3. Image transfer

- pickle stores `data: bytes`;
- JSON stores `encoding: "base64"`;
- Pillow draws the preview (wx may not open WebP);
- on receive, bytes are written to `artifacts/` and shown again.

![WebP preview](screenshots/lab1_webp.png)

![Lab 1 window](screenshots/lab1.png)

## 4. Results

`python main.py --lab 1` writes both files, reads them with the reader, and echoes on localhost:8003. Tests cover a 5000-byte frame and WebP bytes after JSON.

## 5. Conclusions

Serialization lets an object survive a process boundary and a socket. pickle is convenient inside Python; JSON is the boundary format. Images in JSON need base64. Frame length must be explicit.

## 6. Control questions

1. **What is serialization/deserialization?**  
   Object → byte stream and back.

2. **Which platforms are used?**  
   pickle and JSON here. The lecture also mentions marshal; other stacks use Java Serializable, System.Text.Json, protobuf.

3. **Why serialize?**  
   Persist state, talk between processes/machines, cache, message buffers.

4. **Can you serialize an object that has methods?**  
   Yes. pickle stores the class and instance data; methods come back from the class. JSON stores data only; methods appear when we rebuild `Student`.
